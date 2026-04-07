"""
数据库连接管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
from src.config.settings import settings


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class Database:
    """数据库管理类"""

    def __init__(self):
        self.engine = None
        self.async_session_maker = None

    async def connect(self):
        """连接数据库"""
        try:
            self.engine = create_async_engine(
                settings.DATABASE_ASYNC_URL,
                echo=settings.DEBUG,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
            self.async_session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败：{e}")
            raise

    async def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("数据库连接已关闭")

    def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if not self.async_session_maker:
            raise RuntimeError("数据库未连接")
        return self.async_session_maker()


# 全局数据库实例
database = Database()


async def get_db() -> AsyncSession:
    """依赖注入：获取数据库会话"""
    db = database.get_session()
    try:
        yield db
    finally:
        await db.close()
