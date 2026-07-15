from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from typing import List
from config.database import get_db
from models.daily_log import Attachment, DailyLog
from schemas.daily_log import DailyLogCreate, DailyLogResponse
from routers.auth import get_current_user
from models.user import User
from models.experiment import Experiment
from routers.experiment import log_telemetry_activity  # 🆕 引入我们写好的审计引擎函数
from routers.authorization import require_daily_log_access, require_experiment_access, require_group_member
from utils.uploads import resolve_attachment_path, save_verified_upload

router = APIRouter(prefix="/experiments", tags=["Daily Logs"])

def _claim_attachments(db: Session, names: List[str], user: User, experiment: Experiment, daily_log: DailyLog) -> None:
    if not names:
        return
    attachments = db.query(Attachment).filter(Attachment.storage_name.in_(set(names))).all()
    if len(attachments) != len(set(names)):
        raise HTTPException(status_code=400, detail="One or more attachments do not exist.")
    for attachment in attachments:
        if attachment.owner_id != user.id and user.role != "sys_admin" and attachment.daily_log_id != daily_log.id:
            raise HTTPException(status_code=403, detail="You may only attach files you uploaded.")
        if attachment.daily_log_id not in (None, daily_log.id):
            raise HTTPException(status_code=409, detail="An attachment is already linked to another log.")
        attachment.group_id = experiment.group_id
        attachment.daily_log_id = daily_log.id


# Uploads are unbound until a log claims them. They remain inaccessible to other
# users during that short interval because downloads require an attachment row
# with an authorized group.
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    storage_name, original_name, media_type, size_bytes, digest = await save_verified_upload(file)
    db.add(Attachment(storage_name=storage_name, original_name=original_name, media_type=media_type, size_bytes=size_bytes, sha256=digest, owner_id=current_user.id))
    db.commit()
    return {"filename": storage_name, "original_name": original_name}

# 1b. 粘贴图片专用上传（自动生成 picture_pasted_XXX 文件名）
@router.post("/upload/paste")
async def upload_pasted_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await upload_file(file, db, current_user)

# 2. 物理二进制安全下载与预览
@router.get("/attachments/{filename}")
def download_file(
    filename: str,
    preview: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attachment = db.query(Attachment).filter(Attachment.storage_name == filename).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found.")
    if attachment.group_id is None:
        if attachment.owner_id != current_user.id and current_user.role != "sys_admin":
            raise HTTPException(status_code=403, detail="You are not authorized to access this attachment.")
    else:
        require_group_member(db, current_user, attachment.group_id)
    file_path = resolve_attachment_path(attachment.storage_name)
    
    if preview:
        return FileResponse(
            file_path,
            media_type=attachment.media_type,
            headers={"Content-Disposition": "inline"}
        )
    return FileResponse(file_path, filename=attachment.original_name, media_type=attachment.media_type)



# 3. 创建日志（支持多附件绑定，并在成功时追加行为审计流水）
@router.post("/{experiment_id}/logs", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
def create_experiment_log(
    experiment_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔍 核心新增：顺藤摸瓜，先查出这个日志所属的母体实验项目，拿到标题和团队 ID
    experiment = require_experiment_access(db, current_user, experiment_id)

    new_log = DailyLog(
        experiment_id=experiment_id,
        author_id=current_user.id,
        content=log_data.content,
        participants=log_data.participants
    )
    new_log.attachments = log_data.attachments or []
    if log_data.shift_date:
        new_log.shift_date = log_data.shift_date
    else:
        new_log.shift_date = datetime.utcnow()
    
    experiment.updated_at = datetime.utcnow()
    db.add(new_log)
    db.flush()
    _claim_attachments(db, new_log.attachments, current_user, experiment, new_log)
    db.commit()
    db.refresh(new_log)

    # 🎯 核心新增：在日志持久化成功的瞬间，强行向审计流水表追加一条【日志录入】记录！
    log_telemetry_activity(
        db,
        current_user.id,
        "recorded log in",  # 精准动词
        f"[{experiment.title}]",         # 绑定实验标题
        experiment.group_id              # 传入真实的 group_id 用于主页空间隔离过滤
    )

    return new_log


# 4. 获取指定实验下的全量日志时间线（保持不动）
@router.get("/{experiment_id}/logs", response_model=List[DailyLogResponse])
def get_experiment_logs(
    experiment_id: int,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_experiment_access(db, current_user, experiment_id)
    limit = min(max(limit, 1), 200)
    return db.query(DailyLog).options(selectinload(DailyLog.author)).filter(
        DailyLog.experiment_id == experiment_id
    ).order_by(DailyLog.created_at.desc()).offset(max(offset, 0)).limit(limit).all()


# 5. 修改原有日志（支持增删/清空附件数组，并在成功时追加行为审计流水）
@router.put("/logs/{log_id}", response_model=DailyLogResponse)
def update_experiment_log(
    log_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = require_daily_log_access(db, current_user, log_id)
        
    # 🔍 核心新增：顺藤摸瓜，通过日志关联的 experiment_id 反向捞出母体实验的信息
    experiment = require_experiment_access(db, current_user, log.experiment_id)

    is_authorized = False
    if current_user.role == "sys_admin":
        is_authorized = True
    elif current_user.role == "team_admin":
        if experiment:
            user_group_ids = [g.id for g in current_user.groups]
            if experiment.group_id in user_group_ids:
                is_authorized = True
    else: # member
        if log.author_id == current_user.id:
            is_authorized = True
            
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Permission denied. You are not authorized to edit this log.")
        
    log.content = log_data.content
    log.participants = log_data.participants
    log.attachments = log_data.attachments or []
    _claim_attachments(db, log.attachments, current_user, experiment, log)
    
    if experiment:
        experiment.updated_at = datetime.utcnow()
    db.commit()

    # 🎯 核心新增：在日志修改成功瞬间，向审计流水表追加一条【日志修改】记录！
    log_telemetry_activity(
        db,
        current_user.id,
        "modified log in",  # 精准动词
        f"[{experiment.title if experiment else 'Unknown'}]",             # 绑定实验标题
        experiment.group_id if experiment else None                 # 传入真实的 group_id 用于主页空间隔离过滤
    )

    db.refresh(log)
    return log


# 6. 删除日志
@router.delete("/logs/{log_id}")
def delete_experiment_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = require_daily_log_access(db, current_user, log_id)
        
    # 权限规则：创建者本人，或者超级管理员，或者该实验所属研究组的组长可以删除
    experiment = require_experiment_access(db, current_user, log.experiment_id)
    
    is_authorized = False
    if current_user.role == "sys_admin":
        is_authorized = True
    elif current_user.role == "team_admin":
        if experiment:
            user_group_ids = [g.id for g in current_user.groups]
            if experiment.group_id in user_group_ids:
                is_authorized = True
    else: # member
        if log.author_id == current_user.id:
            is_authorized = True
            
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Permission denied. You are not authorized to delete this log.")
        
    db.delete(log)
    db.commit()
    
    if experiment:
        log_telemetry_activity(
            db,
            current_user.id,
            "deleted a log in",
            f"[{experiment.title}]",
            experiment.group_id
        )
        
    return {"status": "success", "message": "Log deleted successfully"}
