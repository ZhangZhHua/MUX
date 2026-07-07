import json
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"

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