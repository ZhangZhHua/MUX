import json
from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base
# EventTag model to separate event tags from experiment tags
class EventTag(Base):
    __tablename__ = "event_tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

# Event to EventTag many-to-many association
event_tag_association = Table(
    'lab_event_tags_link',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('lab_events.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('event_tags.id', ondelete="CASCADE"), primary_key=True)
)

# Event to User (participants) many-to-many association
event_participant_association = Table(
    'event_participant',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('lab_events.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
)

class LabEvent(Base):
    __tablename__ = "lab_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)      # Event introduction (事件介绍)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="SET NULL"), nullable=True)
    author_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)  # Base date of the event
    end_date = Column(DateTime, nullable=True)     # End date/time of the event
    is_important = Column(Boolean, default=False, nullable=False) # For high-priority milestones
    
    # Attachments can reference existing experiment files or be locally uploaded.
    # Stored as JSON: [{"name": "file.pdf", "url": "/uploads/file.pdf", "is_referenced": True}]
    attachments_json = Column("attachments", Text, nullable=True)
    
    # Recurrence rules
    recurrence_rule = Column(String, nullable=True)       # e.g., "1_week", "2_weeks", or null
    recurrence_end_date = Column(DateTime, nullable=True) # null means default indefinitely (一直存在)
    
    # Exceptions tracker for recurrence overrides
    exception_dates = Column(Text, nullable=True)         # JSON list of exception ISO dates e.g., ["2026-07-14"]
    parent_event_id = Column(Integer, ForeignKey('lab_events.id', ondelete="CASCADE"), nullable=True) # if it's an instance override
    
    created_at = Column(DateTime, default=datetime.utcnow)

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

    # Relationships
    experiment = relationship("Experiment")
    author = relationship("User")
    tags = relationship("EventTag", secondary=event_tag_association)
    participants = relationship("User", secondary=event_participant_association)
    comments = relationship("EventComment", back_populates="event", cascade="all, delete-orphan")


class EventComment(Base):
    __tablename__ = "event_comments"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('lab_events.id', ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("LabEvent", back_populates="comments")
    author = relationship("User")
