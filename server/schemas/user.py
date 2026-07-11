from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- 团队相关数据校验 ---
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_private: bool = False
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True  # 允许兼容 SQLAlchemy 模型




# --- 登录相关数据校验 ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str  # 🆕 新增：登录成功后直接把姓名返给前端，方便前端展示

class UserLogin(BaseModel):
    email: str
    password: str

# --- 提升权限请求校验 ---
class AssignAdminRequest(BaseModel):
    user_id: int
    
# 🆕 新增：专用于修改个人档案的输入校验模型
class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    institution: Optional[str] = None
    country_region: Optional[str] = None
    academic_bio: Optional[str] = None


        
        
        
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr 
    password: str
    first_name: str
    last_name: str
    
    # 🆕 核心修复：允许注册请求中携带群组 ID 列表（默认为 None 或空列表）
    # 这样后端执行 if user_data.group_ids 时就不会触发 AttributeError 崩溃了！
    group_ids: Optional[List[int]] = None

# 🆕 新增：专门用于在用户档案内部嵌套展现的群组微型微型响应体
class GroupMinResponse(BaseModel):
    id: int
    name: str
    is_private: bool = False
    owner_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str] = "Researcher"
    last_name: Optional[str] = ""
    role: Optional[str] = "member"
    phone: Optional[str] = None
    institution: Optional[str] = None
    country_region: Optional[str] = None
    academic_bio: Optional[str] = None
    
    # 🆕 新增字段
    avatar_node: Optional[str] = None  # 头像图片流占位符
    homepage_url: Optional[str] = None # 个人主页跳转预留
    
    # 🆕 核心升级：级联带出该用户在数据库里绑定的所有团队，完美解决“资料页显示隶属团队”的需求
    groups: List[GroupMinResponse] = []

    class Config:
        from_attributes = True