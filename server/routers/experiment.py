from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from config.database import get_db
from models.experiment import Experiment, Tag, Bulletin, ExperimentStep
from schemas.experiment import (
    ExperimentCreate, ExperimentResponse, TagResponse, TagCreate, ExperimentUpdate,
    BulletinCreate, BulletinResponse, ExperimentStepCreate, ExperimentStepUpdate, ExperimentStepResponse
)
from routers.auth import get_current_user
from models.user import User, Group
from schemas.user import UserResponse
from models.intelligence import Notice, ActivityLog
from schemas.intelligence import NoticeCreate, NoticeResponse, ActivityLogResponse


router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.post("", response_model=ExperimentResponse)
def create_experiment(
    exp_data: ExperimentCreate,   # 实验创建数据，包含创建实验所需的所有信息
    db: Session = Depends(get_db),   # 数据库会话，用于与数据库交互
    current_user: User = Depends(get_current_user)  # 当前用户信息，用于权限验证
):
    # 检查用户权限，只有非普通成员才能创建实验项目
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="普通成员无权创建实验项目")
        
    # 创建新的实验实例，使用提供的数据填充各个字段
    # 如果未提供状态，则默认设置为"running"
    new_exp = Experiment(
        group_id=exp_data.group_id,  # 实验所属的组ID
        title=exp_data.title,  # 实验标题
        description=exp_data.description,  # 实验描述
        format_type=exp_data.format_type,  # 实验格式类型
        status=exp_data.status or "running"  # 实验状态，默认为"running"
    )
    # 将新实验添加到数据库会话
    db.add(new_exp)
    # 提交会话，将更改保存到数据库
    db.commit()
    db.refresh(new_exp)
    log_telemetry_activity(
        db, 
        current_user.id, 
        "created a new experiment", 
        f"[{new_exp.title}]", 
        new_exp.group_id
    )
    return new_exp

@router.get("", response_model=List[ExperimentResponse])
def get_experiments(
    group_id: int = 0, # 给定默认值 0
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 如果 group_id 为 0，代表聚合看板模式
    if group_id == 0:
        # 如果非超级管理员，只捞取自己隶属的所有团队的实验；超管则捞取全量
        if current_user.role != "sys_admin":
            my_group_ids = [g.id for g in current_user.groups]
            query = db.query(Experiment).filter(Experiment.group_id.in_(my_group_ids))
        else:
            query = db.query(Experiment)
    else:
        query = db.query(Experiment).filter(Experiment.group_id == group_id)

    if tag:
        query = query.join(Experiment.tags).filter(Tag.name == tag)
    return query.order_by(Experiment.updated_at.desc()).all()

@router.get("/tags", response_model=List[TagResponse])
def get_all_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tag).all()

@router.post("/tags", response_model=TagResponse)
def create_global_tag(
    tag_data: TagCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="普通成员无法创建系统标签")
    
    clean_name = tag_data.name.strip()
    if not clean_name.startswith('#'):
        clean_name = f"#{clean_name}"
        
    existing_tag = db.query(Tag).filter(Tag.name == clean_name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="该标签已存在")
        
    new_tag = Tag(name=clean_name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

@router.get("/{id}", response_model=ExperimentResponse)
def get_single_experiment(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="实验项目未找到")
    return exp

# 🆕 重构：全能更新接口，支持修改大纲、标题、运行状态和标签列表
@router.put("/{id}", response_model=ExperimentResponse)
def update_experiment(
    id: int, 
    update_data: ExperimentUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="实验项目未找到")
    
    if update_data.title is not None:
        exp.title = update_data.title
    if update_data.description is not None:
        exp.description = update_data.description
    if update_data.current_task is not None:
        exp.current_task = update_data.current_task
    if update_data.format_type is not None:
        exp.format_type = update_data.format_type
    if update_data.status is not None:
        exp.status = update_data.status
        
    # 🆕 动态同步标签：若传入标签数组，自动在关联表中全量同步，不存在的标签自动注册
    if update_data.tags is not None:
        db_tags = []
        for tag_name in update_data.tags:
            clean_name = tag_name.strip()
            if not clean_name:
                continue
            if not clean_name.startswith('#'):
                clean_name = f"#{clean_name}"
            
            # 查找或自动注册新标签
            tag_obj = db.query(Tag).filter(Tag.name == clean_name).first()
            if not tag_obj:
                tag_obj = Tag(name=clean_name)
                db.add(tag_obj)
                db.commit()
                db.refresh(tag_obj)
            db_tags.append(tag_obj)
        exp.tags = db_tags
        
    exp.updated_at = datetime.utcnow()
    db.commit()
    log_telemetry_activity(
        db, 
        current_user.id, 
        "modified the ", 
        f"[{exp.title}]", 
        exp.group_id
    )
    db.refresh(exp)
    return exp

@router.put("/{id}/members")
def sync_experiment_members(id: int, user_ids: List[int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exp = db.query(Experiment).filter(Experiment.id == id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="实验项目未找到")
        
    selected_users = db.query(User).filter(User.id.in_(user_ids)).all()
    exp.members = selected_users
    db.commit()
    return {"message": "实验研究人员同步成功"}

@router.get("/groups/{group_id}/members", response_model=List[UserResponse])
def get_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="科研团队未找到")
    return group.members

# 🆕 1. 获取指定实验底下的全位置顶通告
@router.get("/{experiment_id}/bulletins", response_model=List[BulletinResponse])
def get_experiment_bulletins(experiment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Bulletin).filter(Bulletin.experiment_id == experiment_id).order_by(Bulletin.created_at.asc()).all()

def log_telemetry_activity(db: Session, user_id: int, action: str, target: str, group_id: Optional[int] = None):
    try:
        new_log = ActivityLog(
            user_id=user_id,
            action=action,
            target=target,
            group_id=group_id
        )
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"⚠️ Telemetry log failed: {e}")


@router.post("/{experiment_id}/bulletins", response_model=BulletinResponse)
def create_experiment_bulletin(
    experiment_id: int, 
    bulletin_data: BulletinCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="Permission denied. Only operators or admins can post bulletins.")
    
    # 🔍 核心修复：先查询出这个通知所属的母体实验对象
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Target experiment node not found.")
        
    new_bulletin = Bulletin(
        experiment_id=experiment_id,
        text=bulletin_data.text.strip(),
        author=f"{current_user.first_name} {current_user.last_name}"
    )
    db.add(new_bulletin)
    db.commit()
    db.refresh(new_bulletin)
    
    # ⚙️ 核心修复：将动作修正为发布通知，并安全地传入 experiment 的真实属性
    log_telemetry_activity(
        db, 
        current_user.id, 
        "posted a new bulletin in", # 动作修改
        f"[{experiment.title}]",     # 目标修改：使用上面查出来的真实 title
        experiment.group_id          # 组 ID 修改：使用真实的 group_id
    )
    
    return new_bulletin

# 🆕 3. 物理撤销/归档某条特定通知
@router.delete("/bulletins/{bulletin_id}")
def delete_experiment_bulletin(bulletin_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="Permission denied. Only operators or admins can clear bulletins.")
        
    bulletin = db.query(Bulletin).filter(Bulletin.id == bulletin_id).first()
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin notice not found")
        
    db.delete(bulletin)
    db.commit()
    return {"message": "Bulletin notice removed from active board"}

@router.get("/groups") # 或者对应的路径
def get_user_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 确保它能正常返回数据
    return db.query(Group).all()


# 🆕 API 1. 穿透型通知拉取流：根据当前激活团队或聚合模式，级联吐出“系统通知+团队通知”
@router.get("/intelligence/notices", response_model=List[NoticeResponse])
def get_synchronized_notices(group_id: int = 0, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_group_ids = [g.id for g in current_user.groups]
    
    if group_id != 0:
        query = db.query(Notice).filter((Notice.type == "system") | ((Notice.type == "team") & (Notice.group_id == group_id)))
    else:
        if user_group_ids:
            query = db.query(Notice).filter((Notice.type == "system") | ((Notice.type == "team") & (Notice.group_id.in_(user_group_ids))))
        else:
            query = db.query(Notice).filter(Notice.type == "system")
        
    raw_notices = query.order_by(
        case((Notice.type == "system", 0), else_=1).asc(),
        Notice.created_at.desc()
    ).all()
    
    # 扁平化组装发布者姓名及组名
    res = []
    for n in raw_notices:
        res.append(NoticeResponse(
            id=n.id,
            type=n.type,
            group_id=n.group_id,
            content=n.content,
            author_id=n.author_id,
            created_at=n.created_at,
            author_name=f"{n.author.first_name} {n.author.last_name}" if n.author else "System Cluster",
            group_name=n.group.name if (n.type == "team" and n.group) else None
        ))
    return res


# 🆕 API 2. 金字塔特权发布接口：只有管理员能发布通知，且只有超级管理员能给全校发大喇叭
@router.post("/intelligence/notices", response_model=NoticeResponse)
def broadcast_new_notice(payload: NoticeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 🔒 权限哨兵一：拦阻普通研究员的发布企图
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="组织越权。只有实验室管理层能够发布置顶公告。")
        
    # 🔒 权限哨兵二：只有超级管理员 sys_admin 才能发布全局系统大喇叭
    if payload.type == "system" and current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="特权级不足。只有系统超级管理员有权发布全局全校大通告。")
        
    # 🔒 权限哨兵三：如果是普通课题组长，校验其是否对目标组拥有管辖权
    if payload.type == "team" and current_user.role != "sys_admin":
        user_belongs_to_target = any(g.id == payload.group_id for g in current_user.groups)
        if not user_belongs_to_target:
            raise HTTPException(status_code=403, detail="边界越权。您无法向您未主管的课题组注入通知。")

    # 物理持久化写入
    new_notice = Notice(
        type=payload.type,
        group_id=payload.group_id if payload.type == "team" else None,
        content=payload.content.strip(),
        author_id=current_user.id
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    
    return NoticeResponse(
        id=new_notice.id,
        type=new_notice.type,
        group_id=new_notice.group_id,
        content=new_notice.content,
        author_id=new_notice.author_id,
        created_at=new_notice.created_at,
        author_name=f"{current_user.first_name} {current_user.last_name}"
    )


# 🆕 API 3. 悬浮毁灭者接口：自上而下的通知在线安全销毁管道
@router.delete("/intelligence/notices/{notice_id}")
def delete_broadcast_notice(notice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="组织越权。")
        
    target_notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not target_notice:
        raise HTTPException(status_code=404, detail="该通告已被其他节点物理抹除")
        
    # 🔒 权限哨兵：普通组长绝不允许抹除 sys_admin 挂在天上的全局系统通告
    if target_notice.type == "system" and current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="权限封锁：组内负责人无法剥离系统超级管理员发布的全局通告。")
        
    if current_user.role != "sys_admin":
        # 校验该通知是不是属于他管辖的组
        if target_notice.group_id not in [g.id for g in current_user.groups]:
            raise HTTPException(status_code=403, detail="越权隔离：您无权撤销其他课题组的通知公告。")

    db.delete(target_notice)
    db.commit()
    return {"status": "success", "message": "Notice node safely unlinked from central disk."}


# 🆕 API 4. 流式动态时间轴获取端点：自适应刷出审计痕迹
@router.get("/intelligence/activities", response_model=List[ActivityLogResponse])
def get_telemetry_activities_stream(group_id: int = 0, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(ActivityLog)
    
    # 0 聚合看板模式下：只捞取当前用户真正参与的所有团队的动态合集
    if group_id == 0:
        if current_user.role != "sys_admin":
            my_group_ids = [g.id for g in current_user.groups]
            query = query.filter(ActivityLog.group_id.in_(my_group_ids))
    else:
        # 特定物理组过滤
        query = query.filter(ActivityLog.group_id == group_id)
        
    raw_logs = query.order_by(ActivityLog.created_at.desc()).limit(15).all()
    
    return [
        ActivityLogResponse(
            id=l.id,
            user_name=f"{l.author.first_name} {l.author.last_name}" if l.author else "System",
            action=l.action,
            target=l.target,
            group_id=l.group_id,
            created_at=l.created_at
        ) for l in raw_logs
    ]


# --- 实验步骤 (Experiment Steps Checklist) 接口 ---

@router.get("/{experiment_id}/steps", response_model=List[ExperimentStepResponse])
def get_experiment_steps(
    experiment_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db.query(ExperimentStep).filter(ExperimentStep.experiment_id == experiment_id).order_by(ExperimentStep.id.asc()).all()


@router.post("/{experiment_id}/steps", response_model=ExperimentStepResponse)
def create_experiment_step(
    experiment_id: int,
    step_data: ExperimentStepCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="Permission denied. Only operators or admins can manage steps.")
    
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    new_step = ExperimentStep(
        experiment_id=experiment_id,
        title=step_data.title.strip()
    )
    exp.updated_at = datetime.utcnow()
    db.add(new_step)
    db.commit()
    db.refresh(new_step)
    return new_step


@router.put("/{experiment_id}/steps/{step_id}", response_model=ExperimentStepResponse)
def update_experiment_step(
    experiment_id: int,
    step_id: int,
    step_data: ExperimentStepUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    step = db.query(ExperimentStep).filter(
        ExperimentStep.id == step_id, 
        ExperimentStep.experiment_id == experiment_id
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
        
    # 如果修改标题，只有非普通成员（操作员/管理员）可以操作
    if step_data.title is not None:
        if current_user.role == "member":
            raise HTTPException(status_code=403, detail="Only admins can modify step titles.")
        step.title = step_data.title.strip()
        
    # 任何人均可勾选/取消勾选完成状态
    if step_data.is_completed is not None:
        step.is_completed = step_data.is_completed
        
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(step)
    return step


@router.delete("/{experiment_id}/steps/{step_id}")
def delete_experiment_step(
    experiment_id: int,
    step_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "member":
        raise HTTPException(status_code=403, detail="Permission denied. Only admins can delete steps.")
        
    step = db.query(ExperimentStep).filter(
        ExperimentStep.id == step_id, 
        ExperimentStep.experiment_id == experiment_id
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
        
    db.delete(step)
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Step deleted successfully"}


@router.delete("/{id}")
def delete_experiment(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied. Only admins can delete experiments.")
        
    experiment = db.query(Experiment).filter(Experiment.id == id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment project not found.")
        
    if current_user.role == "team_admin":
        user_group_ids = [g.id for g in current_user.groups]
        if experiment.group_id not in user_group_ids:
            raise HTTPException(status_code=403, detail="Permission denied. You can only delete experiments in your own research groups.")
            
    log_telemetry_activity(
        db=db,
        user_id=current_user.id,
        action="deleted the experiment",
        target=experiment.title,
        group_id=experiment.group_id
    )
    
    db.delete(experiment)
    db.commit()
    return {"status": "success", "message": "Experiment deleted successfully"}