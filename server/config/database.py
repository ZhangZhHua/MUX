from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# 数据库连接字符串，优先从环境变量读取（容器化部署需要），开发环境回退到 localhost
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://lab_user:lab_password_2026@localhost:5432/lab_logs"
)

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建数据库会话工厂，用于后续的增删改查操作
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 所有数据模型（Models）的基类
Base = declarative_base()

# 获取数据库会话的工具函数（依赖注入时会用到）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()