from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


# 实验与标签的多对多关联表
experiment_tag_association = Table(
    'experiment_tag',
    Base.metadata,
    Column('experiment_id', Integer, ForeignKey('experiments.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

# 实验与人员的多对多关联表
experiment_user_association = Table(
    'experiment_user',
    Base.metadata,
    Column('experiment_id', Integer, ForeignKey('experiments.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
)

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id', ondelete="CASCADE"), nullable=False)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    current_task = Column(Text, default="", nullable=True)
    format_type = Column(String, default="markdown")
    
    # 💡 关键：请绝对确保这一行存在并保存了！有了它，SQLAlchemy 才能识别 status 参数
    status = Column(String, default="running", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("Group")
    tags = relationship("Tag", secondary=experiment_tag_association, back_populates="experiments")
    members = relationship("User", secondary=experiment_user_association)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    experiments = relationship("Experiment", secondary=experiment_tag_association, back_populates="tags")


class Bulletin(Base):
    __tablename__ = "bulletins"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExperimentStep(Base):
    __tablename__ = "experiment_steps"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment")