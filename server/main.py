from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 1. 引入跨域中间件
import os
import models.user as user_model
from routers import auth
import models.experiment as exp_model # 🆕 引入实验模型
from routers import auth, experiment # 🆕 引入实验路由
import models.daily_log as log_model # 🆕 1. 引入日志模型
import models.intelligence as intel_model # 🆕 引入安全审计与系统设置模型
import models.event as event_model # 🆕 引入周日程与大事记模型
from routers import auth, experiment, daily_log, event, backup

app = FastAPI(title="Physics Lab Log System API")

# 2. 配置跨域支持（必须挂载在路由 include_router 之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法 (包含 OPTIONS, POST, GET 等)
    allow_headers=["*"],  # 允许所有请求头
)

# 挂载路由模块
app.include_router(auth.router, prefix="/api")
app.include_router(experiment.router, prefix="/api")
app.include_router(daily_log.router, prefix="/api")
app.include_router(event.router, prefix="/api")
app.include_router(backup.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Lab Log System API is online."}
