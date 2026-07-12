from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config.database import get_db
from models.user import User, Group
from models.intelligence import SystemSetting
from schemas.user import UserCreate, UserResponse, GroupCreate, GroupResponse, UserLogin, Token, AssignAdminRequest, ProfileUpdate
from schemas.intelligence import SystemSettingUpdate, SystemSettingResponse
from utils.security import get_password_hash, verify_password, create_access_token, decode_access_token
from fastapi.security import  OAuth2PasswordRequestForm # <- 确保引入了这个
from typing import List
from datetime import datetime, timedelta


router = APIRouter(prefix="/auth", tags=["Authentication"])

# 定义从请求头中获取 Token 的规则（Authorization: Bearer <TOKEN>）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- 守卫函数：获取当前登录用户 ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Wrong-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    user.last_active_at = datetime.utcnow()
    db.commit()
    return user


# --- 1. 用户注册 ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    total_users = db.query(User).count()
    assigned_role = "sys_admin" if total_users == 0 else "member"

    hashed_pwd = get_password_hash(user_data.password)
    
    # Check if registration requires approval
    require_approval_setting = db.query(SystemSetting).filter(SystemSetting.key == "require_approval").first()
    require_approval = require_approval_setting and require_approval_setting.value.lower() == "true"
    user_status = "pending" if require_approval else "active"
    
    # 实例化时存入用户的姓和名
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=assigned_role,
        status=user_status
    )

    if user_data.group_ids:
        associated_groups = db.query(Group).filter(Group.id.in_(user_data.group_ids)).all()
        new_user.groups = associated_groups

    db.add(new_user)
    db.flush()  # 先 flush 以获取 new_user.id
    
    # 自动创建私人 Group
    private_name = f"[Private] {new_user.first_name} {new_user.last_name}"
    counter = 1
    while db.query(Group).filter(Group.name == private_name).first():
        private_name = f"[Private] {new_user.first_name} {new_user.last_name} ({counter})"
        counter += 1
    
    private_group = Group(
        name=private_name,
        description=f"Personal workspace for {new_user.first_name} {new_user.last_name}",
        is_private=True,
        owner_id=new_user.id
    )
    db.add(private_group)
    db.flush()
    
    # 将用户加入自己的私人 Group
    new_user.groups.append(private_group)
    db.commit()
    db.refresh(new_user)
    return new_user


# 2. 修改后的登录接口
@router.post("/login", response_model=Token)
def login(login_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.username).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Check pending/rejected status
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Your account is pending admin approval.")
    if user.status == "rejected":
        raise HTTPException(status_code=403, detail="Your account registration has been rejected.")
    
    # Update last active
    user.last_active_at = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.email})
    
    # 🆕 拼接英文姓名（通常是 First Name + Last Name）
    full_name = f"{user.first_name} {user.last_name}"
    
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role,
        "full_name": full_name,  # 🆕 返回给前端
        "user_id": user.id
    }

# --- 3. 指定团队管理员（仅限系统管理员操作） ---
@router.put("/assign-team-admin")
def assign_team_admin(
    request_data: AssignAdminRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)  # 拦截器：先验证是否登录
):
    # 严格鉴权：只有系统管理员有此权限
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Permission denied. Only System Admins can perform this action.")
    
    # 查找目标用户
    target_user = db.query(User).filter(User.id == request_data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=44, detail="Target user not found.")
    
    if target_user.role == "sys_admin":
        raise HTTPException(status_code=400, detail="Cannot change the role of a System Admin.")

    # 变更角色为团队管理员
    target_user.role = "team_admin"
    db.commit()
    return {"message": f"User {target_user.email} has been successfully promoted to team_admin."}


# --- 4. 临时创建团队接口 ---
@router.post("/groups", response_model=GroupResponse)
def create_group(group_data: GroupCreate, db: Session = Depends(get_db)):
    existing_group = db.query(Group).filter(Group.name == group_data.name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already exists.")
    new_group = Group(name=group_data.name, description=group_data.description)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group



# 🆕 1. 获取当前登录科学家的完整最新档案
@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

# 🆕 2. 在线修改并持久化更新个人资料
@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    profile_data: ProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    current_user.first_name = profile_data.first_name.strip()
    current_user.last_name = profile_data.last_name.strip()
    current_user.phone = profile_data.phone.strip() if profile_data.phone else None
    current_user.institution = profile_data.institution.strip() if profile_data.institution else None
    current_user.country_region = profile_data.country_region.strip() if profile_data.country_region else None
    current_user.academic_bio = profile_data.academic_bio.strip() if profile_data.academic_bio else None
    
    db.commit()
    db.refresh(current_user)
    
    # 同步让前端持有的 Session 缓存更新
    return current_user

# 🆕 新增：实验室主管/系统管理员在线动态变更其他成员权限权限接口
@router.put("/users/{user_id}/role")
def update_user_system_role(
    user_id: int, 
    role_payload: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 🔒 安全防线：校验当前发起操作的人是否具备管理级硬核身份
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="权限不足。只有实验室负责人或系统管理员能够调整他人科研权限。")

    # 🛡️ 禁止自己改自己的角色（防死锁）
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="您不能修改自己的角色权限。请联系另一位管理员操作。")

    # 检索目标篡改对象
    target_member = db.query(User).filter(User.id == user_id).first()
    if not target_member:
        raise HTTPException(status_code=404, detail="在当前组织内未检索到该科研人员档案")

    new_role = role_payload.get("role")
    if new_role not in ["sys_admin", "team_admin", "member"]:
        raise HTTPException(status_code=400, detail="不合法的组织权限配置项")

    # 🚫 team_admin 不能授予 sys_admin 角色（仅 sys_admin 有此权限）
    if current_user.role == "team_admin" and new_role == "sys_admin":
        raise HTTPException(status_code=403, detail="权限不足。只有系统超级管理员（sys_admin）可以授予 sys_admin 角色。")

    # 🚫 team_admin 只能修改自己组内成员的角色
    if current_user.role == "team_admin":
        current_group_ids = {g.id for g in current_user.groups}
        target_group_ids = {g.id for g in target_member.groups}
        if not current_group_ids & target_group_ids:
            raise HTTPException(status_code=403, detail="权限不足。您只能修改本课题组内成员的角色权限。")

    # 物理执行变更并提交事务锁
    target_member.role = new_role
    db.commit()
    
    return {
        "message": f"Scientist {target_member.first_name} has been reassigned to {new_role} successfully.",
        "updated_user_id": user_id,
        "new_role": new_role
    }
    
    
# 🆕 新增：只有系统超级管理员（sys_admin）才能凭空孵化全新的科研团队
@router.post("/groups", response_model=GroupResponse)
def create_new_research_group(
    group_data: GroupCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 🔒 安全硬核护栏：无情拦截非 sys_admin 的越权尝试
    if current_user.role != "sys_admin":
        raise HTTPException(
            status_code=403, 
            detail="组织架构越权。只有系统超级管理员（sys_admin）可以开辟全新的独立科研群组。"
        )
        
    # 检查重名冲突，保证 PostgreSQL 唯一性约束
    existing_group = db.query(Group).filter(Group.name == group_data.name.strip()).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="该物理课题组名称在系统注册表中心已存在")
        
    # 物理写入群组磁盘
    new_group = Group(
        name=group_data.name.strip(),
        description=group_data.description.strip() if group_data.description else None
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    # 💡 联动：自动将创建该组的超级管理员自己也先塞入该组，防止无主死锁
    new_group.members.append(current_user)
    db.commit()
    
    return new_group

# 1. Get all registered users (for admin selection)
@router.get("/users", response_model=List[UserResponse])
def get_all_registered_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).order_by(User.first_name.asc()).all()

# 2. Add a user to a specific group
@router.post("/groups/{group_id}/members")
def add_scientist_to_group_cluster(
    group_id: int, 
    payload: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Access control: Admins only
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied. Admin privileges required.")
        
    target_user_id = payload.get("user_id")
    if not target_user_id:
        raise HTTPException(status_code=400, detail="Missing user_id in payload.")
        
    # Verify group and user existence
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Target group not found.")
        
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Prevent duplicate members
    if user in group.members:
        raise HTTPException(status_code=400, detail="User is already a member of this group.")
        
    # Append member and commit
    group.members.append(user)
    db.commit()
    
    return {"status": "success", "message": f"Successfully enrolled {user.first_name} into {group.name} cluster."}


# 🆕 1. 重构全量群组拉取接口（覆盖或更新原有的获取群组逻辑）
@router.get("/groups", response_model=List[GroupResponse])
def get_user_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    自上而下的穿透判定：
    - 如果是 sys_admin (超级管理员)，直接无视任何绑定，放行并吐出系统中【全量】已注册的物理课题组。
    - 如果是普通科研人员/PI，则精确返回其【自身隶属】的团队。
    """
    if current_user.role == "sys_admin":
        return db.query(Group).order_by(Group.name.asc()).all()
    
    # 普通用户：返回自己的所有组，但过滤掉别人的私人Group
    visible_groups = []
    for g in current_user.groups:
        if g.is_private and g.owner_id != current_user.id:
            continue  # Skip other users' private groups
        visible_groups.append(g)
    
    # Also include user's own private group if not already included
    own_private = db.query(Group).filter(
        Group.is_private == True, 
        Group.owner_id == current_user.id
    ).first()
    if own_private and own_private not in visible_groups:
        visible_groups.append(own_private)
    
    return sorted(visible_groups, key=lambda g: g.name)


# 🆕 2. 新增：将指定科学家从某个课题组编制中物理移除（组织瘦身与反锁死断路器）
@router.delete("/groups/{group_id}/members/{user_id}")
def remove_scientist_from_group_cluster(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🛡️ 边界断路器一：绝对禁止在成员页自己开除自己，防止管理权死锁
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="安全死锁限制：您无法将自己从当前课题组编制中移除。")
        
    # 🔒 权限哨兵判定：除了超级管理员，只有本组内的 team_admin (PI) 有资格进行人员裁撤
    if current_user.role != "sys_admin":
        is_owner_of_group = any(g.id == group_id for g in current_user.groups)
        if current_user.role != "team_admin" or not is_owner_of_group:
            raise HTTPException(status_code=403, detail="组织越权。只有本实验室负责人或超级管理员有权调整编制。")
            
    # 检索物理实体
    group = db.query(Group).filter(Group.id == group_id).first()
    target_scientist = db.query(User).filter(User.id == user_id).first()
    
    if not group or not target_scientist:
        raise HTTPException(status_code=404, detail="未检索到对应的团队或研究人员档案节点")
        
    # 🛡️ 边界断路器二：下属绝对不能开除上司（普通 PI 无法踢出进组视察的 sys_admin）
    if target_scientist.role == "sys_admin" and current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="特权级冲突：您无权撤销系统超级管理员的课题组编制。")
        
    # 执行物理剥离
    if target_scientist in group.members:
        group.members.remove(target_scientist)
        db.commit()
        return {
            "status": "success",
            "message": f"Scientist {target_scientist.first_name} has been successfully de-enrolled from {group.name}."
        }
        
    raise HTTPException(status_code=400, detail="该人员目前本身并不属于此研究团队")


# 🆕 3. 新增：用户自助在线更新绑定自己的学术头像与外部个人主页
@router.put("/profile/academic-identity")
def update_personal_academic_identity(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    允许任何登录的科学家随时修改其头像节点引用以及个人主页 URL。
    """
    user_node = db.query(User).filter(User.id == current_user.id).first()
    
    if "avatar_node" in payload:
        user_node.avatar_node = payload.get("avatar_node")
        
    if "homepage_url" in payload:
        url = payload.get("homepage_url", "").strip()
        user_node.homepage_url = url if url else None
        
    db.commit()
    return {
        "status": "success", 
        "message": "Academic identity updated tokens preserved.",
        "avatar_node": user_node.avatar_node,
        "homepage_url": user_node.homepage_url
    }


@router.get("/system-settings/{key}", response_model=SystemSettingResponse)
def get_system_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        # 默认值
        defaults = {
            "help_info": "For technical support or issues, please contact the administrator at admin@physics-lab.org.",
            "session_timeout": "120",
            "require_approval": "false",
        }
        default_val = defaults.get(key, "")
        setting = SystemSetting(key=key, value=default_val)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.put("/system-settings/{key}", response_model=SystemSettingResponse)
def update_system_setting(
    key: str, 
    payload: SystemSettingUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "sys_admin":
        raise HTTPException(status_code=403, detail="Permission denied. Only System Admins can change settings.")
    
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        setting = SystemSetting(key=key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()
    db.refresh(setting)
    return setting
    return setting


# --- User Approval & Session Management ---

@router.get("/users/pending")
def get_pending_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied.")
    if current_user.role == "sys_admin":
        users = db.query(User).filter(User.status == "pending").all()
    else:
        user_group_ids = [g.id for g in current_user.groups]
        all_pending = db.query(User).filter(User.status == "pending").all()
        users = [u for u in all_pending if any(g.id in user_group_ids for g in u.groups)]
    return [UserResponse.from_orm(u) for u in users]


@router.put("/users/{user_id}/approve")
def approve_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.status != "pending":
        raise HTTPException(status_code=400, detail="User is not in pending status.")
    user.status = "active"
    db.commit()
    return {"status": "success", "message": f"User {user.email} approved."}


@router.put("/users/{user_id}/reject")
def reject_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ["sys_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Permission denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.status != "pending":
        raise HTTPException(status_code=400, detail="User is not in pending status.")
    user.status = "rejected"
    db.commit()
    return {"status": "success", "message": f"User {user.email} rejected."}


@router.get("/users/session-status")
def check_session_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    timeout_str = db.query(SystemSetting).filter(SystemSetting.key == "session_timeout").first()
    timeout_minutes = int(timeout_str.value) if timeout_str else 120
    now = datetime.utcnow()
    is_timed_out = False
    if current_user.last_active_at:
        elapsed = (now - current_user.last_active_at).total_seconds() / 60
        is_timed_out = elapsed > timeout_minutes
    return {
        "session_timeout_minutes": timeout_minutes,
        "last_active_at": current_user.last_active_at.isoformat() if current_user.last_active_at else None,
        "is_timed_out": is_timed_out
    }

# --- 公开 Group 列表（注册页调用，无需登录） ---
@router.get("/public-groups", response_model=List[GroupResponse])
def get_public_groups(db: Session = Depends(get_db)):
    """返回所有非私有的 Group，供注册页面展示"""
    groups = db.query(Group).filter(Group.is_private == False).order_by(Group.name.asc()).all()
    return groups
