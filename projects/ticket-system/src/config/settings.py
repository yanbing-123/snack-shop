"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "火车票抢票系统"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str
    DATABASE_ASYNC_URL: str

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""

    # JWT 配置
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 加密配置
    ENCRYPTION_KEY: str

    # CORS 配置
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 12306 配置
    RAILWAY_USERNAME: str = ""
    RAILWAY_PASSWORD: str = ""

    # 通知服务配置
    SMTP_SERVER: str = "smtp.qq.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_EMAIL: str = ""

    # 短信服务配置
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_PHONE_NUMBER: str = ""

    # 打码平台配置
    CAPTCHA_PLATFORM: str = ""
    CAPTCHA_API_KEY: str = ""

    # 频率限制配置 (防封号)
    QUERY_INTERVAL_SECONDS: int = 3
    MONITOR_MIN_INTERVAL_SECONDS: int = 30
    MAX_RETRY_ATTEMPTS: int = 3

    class Config:
        env_file = "config/.env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
