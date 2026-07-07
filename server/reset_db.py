# 文件路径：server/reset_db.py
from sqlalchemy import text
from config.database import engine, Base

# 1. 显式导入所有最新的核心物理模型，确保 SQLAlchemy Metadata 能够完全加载它们
import models.user
import models.experiment
import models.daily_log

print("🔄 [USTC Lab] Initializing database destruction & cleanup pipeline...")

# 2. 严格按依赖反向排列的清空队列（配合 CASCADE 形成双重保险，粉碎一切历史脏数据）
drop_tables = [
    "bulletins",           # 🆕 置顶通知表
    "daily_logs",          # 实验日志时间轴表
    "experiment_user",     # 实验-人员多对多关联表
    "experiment_tag",      # 实验-标签多对多关联表
    "experiments",         # 实验项目主表
    "tags",                # 系统标签全局表
    "group_users",         # 团队-人员多对多关联表
    "users",               # 用户账户凭证主表（含最新 phone/institution 等物理列）
    "groups"               # 科研团队/群组表
]

try:
    with engine.connect() as conn:
        # 开启物理事务隔离锁
        with conn.begin():
            for table in drop_tables:
                print(f"🗑️ Force dropping table if exists: [{table}] via CASCADE...")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
        print("✅ Core layer: All legacy tables and constraints cleanly dropped.")
except Exception as e:
    print(f"⚠️ Warning during table drop sequence: {str(e)}")

# 3. 读取最新的 Python Class 映射，重新在 PostgreSQL 中物理建表
print("🚀 Recreating all tables with modern infrastructure schemas...")
try:
    Base.metadata.create_all(bind=engine)
    print("\n✨ [Success] Database structural alignment complete!")
    print("✨ All tables updated with 'status', 'attachments(JSON)' and 'User Profile Profile' fields!")
except Exception as e:
    print(f"❌ Table infrastructure replication failed: {str(e)}")