from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NoticeCreate(BaseModel):
    type: str # "system" or "team"
    group_id: Optional[int] = None
    content: str

class NoticeResponse(BaseModel):
    id: int
    type: str
    group_id: Optional[int] = None
    content: str
    author_id: int
    created_at: datetime
    author_name: Optional[str] = None # 用于扁平化传递发布者姓名
    group_name: Optional[str] = None # 🆕 用于扁平化传递组名称

    class Config:
        from_attributes = True

class ActivityLogResponse(BaseModel):
    id: int
    user_name: str
    action: str
    target: str
    group_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemSettingUpdate(BaseModel):
    value: str


class SystemSettingResponse(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True