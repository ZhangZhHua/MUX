import json
from sqlalchemy import CheckConstraint, Column, Integer, Text, ForeignKey, DateTime, Index, String
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (
        CheckConstraint("shift_date IS NOT NULL", name="ck_daily_logs_shift_date"),
        Index('ix_daily_logs_experiment_created', 'experiment_id', 'created_at'),
        Index('ix_daily_logs_author', 'author_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    participants = Column(Text, nullable=True)
    
    # 🆕 核心修复：补上漏掉的 created_at 物理列，彻底消灭 AttributeError!
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    shift_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 多附件底层列：存储 JSON 序列化的文件列表
    attachments_json = Column("attachments", Text, nullable=True)

    @property
    def attachments(self):
        if not self.attachments_json:
            return []
        try:
            return json.loads(self.attachments_json)
        except Exception:
            return []

    @attachments.setter
    def attachments(self, value):
        self.attachments_json = json.dumps(value) if value else json.dumps([])

    experiment = relationship("Experiment")
    author = relationship("User")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    storage_name = Column(String, unique=True, nullable=False, index=True)
    original_name = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete="CASCADE"), nullable=True, index=True)
    daily_log_id = Column(Integer, ForeignKey('daily_logs.id', ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User")
    group = relationship("Group")
    daily_log = relationship("DailyLog")
