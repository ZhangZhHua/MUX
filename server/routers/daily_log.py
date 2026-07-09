import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from config.database import get_db
from models.daily_log import DailyLog
from schemas.daily_log import DailyLogCreate, DailyLogResponse
from routers.auth import get_current_user
from models.user import User
from models.experiment import Experiment  # 🆕 用于顺藤摸瓜查实验标题
from routers.experiment import log_telemetry_activity  # 🆕 引入我们写好的审计引擎函数
from utils.security import decode_access_token  # 🆕 引入 token 解密工具

router = APIRouter(prefix="/experiments", tags=["Daily Logs"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

from typing import List, Optional

# 🆕 双通身份验证依赖守卫 (失败时返回 None 而不是抛出异常，交给端点自行判定是否必须拦截)
def get_current_user_from_header_or_query(
    request: Request,
    token: str = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    actual_token = token
    if not actual_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            actual_token = auth_header.split(" ")[1]
            
    if not actual_token:
        return None
        
    try:
        payload = decode_access_token(actual_token)
        if payload is None:
            return None
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception:
        return None

# 1. 物理二进制文件流上传
@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        # Check size limit: 50MB (50 * 1024 * 1024 bytes)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attachment size exceeds the maximum limit of 50MB"
            )

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return {"filename": file.filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File write error on lab server: {str(e)}")

# 2. 物理二进制安全下载与预览
@router.get("/attachments/{filename}")
def download_file(
    filename: str,
    preview: bool = False,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_header_or_query)
):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested telemetry file not found on server")
    
    # 验证权限 (只针对非公开头像的文件进行限制)
    is_avatar = db.query(User).filter(User.avatar_node == filename).first() is not None
    if not is_avatar:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is missing or invalid. Access denied."
            )
            
        daily_log = db.query(DailyLog).filter(DailyLog.attachments_json.like(f"%{filename}%")).first()
        if daily_log:
            experiment = daily_log.experiment
            if current_user.role != "sys_admin":
                user_group_ids = [g.id for g in current_user.groups]
                if experiment.group_id not in user_group_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden: You are not authorized to access this experiment's files."
                    )
    
    if preview:
        import mimetypes
        media_type, _ = mimetypes.guess_type(file_path)
        if not media_type:
            if filename.lower().endswith('.pdf'):
                media_type = "application/pdf"
            else:
                media_type = "application/octet-stream"
        return FileResponse(
            file_path,
            media_type=media_type,
            headers={"Content-Disposition": "inline"}
        )
    return FileResponse(file_path, filename=filename)



# 3. 创建日志（支持多附件绑定，并在成功时追加行为审计流水）
@router.post("/{experiment_id}/logs", response_model=DailyLogResponse, status_code=status.HTTP_201_CREATED)
def create_experiment_log(
    experiment_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔍 核心新增：顺藤摸瓜，先查出这个日志所属的母体实验项目，拿到标题和团队 ID
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Target experiment node not found.")

    new_log = DailyLog(
        experiment_id=experiment_id,
        author_id=current_user.id,
        content=log_data.content,
        participants=log_data.participants
    )
    new_log.attachments = log_data.attachments
    if log_data.shift_date:
        new_log.shift_date = log_data.shift_date
    else:
        new_log.shift_date = datetime.utcnow()
    
    experiment.updated_at = datetime.utcnow()
    db.add(new_log)
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
def get_experiment_logs(experiment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(DailyLog).filter(DailyLog.experiment_id == experiment_id).order_by(DailyLog.created_at.desc()).all()


# 5. 修改原有日志（支持增删/清空附件数组，并在成功时追加行为审计流水）
@router.put("/logs/{log_id}", response_model=DailyLogResponse)
def update_experiment_log(
    log_id: int,
    log_data: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log record not found")
        
    if log.author_id != current_user.id and current_user.role == "member":
        raise HTTPException(status_code=403, detail="Permission denied. You can only edit your own logs.")
        
    log.content = log_data.content
    log.participants = log_data.participants
    log.attachments = log_data.attachments 
    
    # 🔍 核心新增：顺藤摸瓜，通过日志关联的 experiment_id 反向捞出母体实验的信息
    experiment = db.query(Experiment).filter(Experiment.id == log.experiment_id).first()
    
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
    log = db.query(DailyLog).filter(DailyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log record not found")
        
    # 权限规则：创建者本人，或者超级管理员，或者该实验所属研究组的组长可以删除
    experiment = db.query(Experiment).filter(Experiment.id == log.experiment_id).first()
    
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