"""
火车票抢票系统 - 主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from datetime import datetime
import sys

from src.config.settings import settings
from src.api.routes import auth, tickets, monitor, orders, passengers
from src.core.database import database
from src.utils.middleware import RateLimitMiddleware

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=settings.LOG_LEVEL,
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",
)

# 创建 FastAPI 应用
app = FastAPI(
    title="火车票抢票系统",
    description="实时余票监控与自动抢票系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制中间件
app.add_middleware(RateLimitMiddleware)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全局异常：{exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "timestamp": int(datetime.now().timestamp() * 1000),
        },
    )


# 生命周期事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("应用启动中...")
    await database.connect()
    logger.info("数据库连接成功")
    # 初始化 Redis 连接
    # 初始化 Celery
    logger.info("应用启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("应用关闭中...")
    await database.disconnect()
    logger.info("数据库连接已关闭")


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": int(datetime.now().timestamp() * 1000)}


# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["车次查询"])
app.include_router(monitor.router, prefix="/api/v1/monitor", tags=["监控任务"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["订单管理"])
app.include_router(passengers.router, prefix="/api/v1/passengers", tags=["乘车人管理"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
