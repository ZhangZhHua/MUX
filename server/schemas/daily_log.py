from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List # 🆕 引入 List
from schemas.user import UserResponse

class DailyLogCreate(BaseModel):
    content: str
    participants: Optional[str] = None
    attachments: Optional[List[str]] = [] # 🆕 由 Optional[str] 升级为 Optional[List[str]]
    shift_date: Optional[datetime] = None # 🆕 支持指定看板所属班次日期

class DailyLogResponse(BaseModel):
    id: int
    experiment_id: int
    author_id: int
    content: str
    participants: Optional[str]
    attachments: Optional[List[str]] = [] # 🆕 由 Optional[str] 升级为 Optional[List[str]]
    created_at: datetime
    shift_date: datetime                   # 🆕 返回班次日期
    author: UserResponse

    class Config:
        from_attributes = True