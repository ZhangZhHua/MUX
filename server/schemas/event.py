from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from schemas.user import UserResponse, GroupMinResponse
from schemas.experiment import TagResponse  # 🆕 Let's check if TagResponse exists or define a simple one

class EventTagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    title: str
    description: str
    experiment_id: Optional[int] = None
    group_id: int  # Event belongs to a specific research group
    start_date: datetime
    end_date: Optional[datetime] = None
    is_important: Optional[bool] = False
    attachments: Optional[List[dict]] = []  # List of {"name": str, "url": str, "is_referenced": bool}
    recurrence_rule: Optional[str] = None  # None, "weekly", "biweekly", "monthly"
    recurrence_end_date: Optional[datetime] = None
    tags: Optional[List[str]] = []          # List of tag names to link/create
    participants: Optional[List[int]] = []  # List of participant user IDs

class EventResponse(BaseModel):
    id: int
    title: str
    description: str
    experiment_id: Optional[int] = None
    experiment_title: Optional[str] = None
    author_id: int
    author: UserResponse
    group_id: int
    group: Optional[GroupMinResponse] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    is_important: bool
    attachments: List[dict] = []
    recurrence_rule: Optional[str] = None
    recurrence_end_date: Optional[datetime] = None
    exception_dates: Optional[str] = None
    parent_event_id: Optional[int] = None
    created_at: datetime
    tags: List[EventTagResponse] = []
    participants: List[UserResponse] = []
    instance_date: Optional[str] = None     # Dynamically injected when expanding recurrence "YYYY-MM-DD"
    unique_key: Optional[str] = None        # Dynamically injected "id_YYYY-MM-DD"

    class Config:
        from_attributes = True

class EventCommentCreate(BaseModel):
    content: str

class EventCommentResponse(BaseModel):
    id: int
    event_id: int
    author_id: int
    author: UserResponse
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
