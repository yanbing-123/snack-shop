"""
用户认证模块
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from src.core.database import Base
import bcrypt
import jwt
from src.config.settings import settings


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    railway_accounts = relationship("RailwayAccount", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    monitor_tasks = relationship("MonitorTask", back_populates="user", cascade="all, delete-orphan")
    passengers = relationship("Passenger", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def create_access_token(self, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        payload = {
            "sub": str(self.id),
            "username": self.username,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def create_refresh_token(self) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(self.id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class RailwayAccount(Base):
    """12306 账号模型"""
    __tablename__ = "railway_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    password_encrypted = Column(String(255), nullable=False)  # 加密存储
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    user = relationship("User", back_populates="railway_accounts")


class Passenger(Base):
    """乘车人模型"""
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    id_type = Column(String(20), default="ID_CARD")  # ID_CARD, PASSPORT, etc.
    id_number = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    passenger_type = Column(String(20), default="ADULT")  # ADULT, CHILD, STUDENT
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    user = relationship("User", back_populates="passengers", foreign_keys=[user_id])
