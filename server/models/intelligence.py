
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


# 🆕 1. 物理通知/公告数据表
class Notice(Base):
    __tablename__ = "notices"
    __table_args__ = (Index('ix_notices_group_type_created', 'group_id', 'type', 'created_at'),)

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="team") # "system" (全局强穿透置顶) 或 "team" (课题组局部联动)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True) # 如果是 system 级则为 Null
    content = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 级联关系映射
    author = relationship("User")
    group = relationship("Group")

# 🆕 2. 自动化审计流水线数据表（高可扩展：支持后续无限追加更多事项）
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (Index('ix_activity_logs_group_created', 'group_id', 'created_at'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # 例如: "created a new experiment", "modified a shift log", "uploaded a datafile"
    target = Column(String, nullable=False)  # 被操作对象的名称或编号，如 "#RPC-Cryo-Test"
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)
