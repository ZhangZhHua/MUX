from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime
from schemas.user import UserResponse, GroupMinResponse # 🆕 引入 UserResponse, GroupMinResponse
# 标签的返回规范
class TagResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True
# 🆕 新增：专门用于独立创建标签的校验模型
class TagCreate(BaseModel):
    name: str
# 创建实验的输入规范
class ExperimentCreate(BaseModel):
    group_id: int
    title: str
    description: Optional[str] = None
    format_type: Optional[str] = "markdown"
    status: Literal["running", "paused", "completed", "archived"] = "running"

class ExperimentUpdate(BaseModel):
    title: Optional[str] = None          # 🆕 支持更新标题
    description: Optional[str] = None
    current_task: Optional[str] = None   # 🆕 支持更新正在执行的任务
    format_type: Optional[str] = None
    status: Optional[Literal["running", "paused", "completed", "archived"]] = None
    tags: Optional[List[str]] = None     # 🆕 支持同步更新关联的标签列表

class ExperimentResponse(BaseModel):
    id: int
    group_id: int
    title: str
    description: Optional[str]
    current_task: Optional[str] = ""     # 🆕 响应报文中包含目前正在执行的任务
    format_type: str
    status: str                          # 🆕 响应报文中包含当前状态
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []
    members: List[UserResponse] = []
    group: Optional[GroupMinResponse] = None # 🆕 级联携带团队基本信息

    class Config:
        from_attributes = True
    
    
# 🆕 新增：创建公告时前端传来的表单规范
class BulletinCreate(BaseModel):
    text: str

# 🆕 新增：后端返回给前端的完整公告卡片规范
class BulletinResponse(BaseModel):
    id: int
    experiment_id: int
    text: str
    author: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExperimentStepCreate(BaseModel):
    title: str


class ExperimentStepUpdate(BaseModel):
    title: Optional[str] = None
    is_completed: Optional[bool] = None


class ExperimentStepResponse(BaseModel):
    id: int
    experiment_id: int
    title: str
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True
