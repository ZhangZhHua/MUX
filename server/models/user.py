from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from config.database import Base

# 用户与团队的多对多关联表
group_users_association = Table(
    'group_users',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id', ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, default="member")  # sys_admin, team_admin, member

    # 🆕 专家级扩充：工业级用户档案物理字段
    phone = Column(String, nullable=True)
    institution = Column(String, nullable=True)      # 科研机构/单位 (如 USTC, CERN)
    country_region = Column(String, nullable=True)   # 国家与地区
    academic_bio = Column(Text, nullable=True)       # 学术简介 / 研究方向
    # 🆕 新增：物理头像存储节点文件名（例如：avatar_123.png）
    avatar_node = Column(String, nullable=True)
    
    # 🆕 新增：学术个人主页外部链接
    homepage_url = Column(String, nullable=True)
    groups = relationship("Group", secondary=group_users_association, back_populates="members")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    members = relationship("User", secondary=group_users_association, back_populates="groups")