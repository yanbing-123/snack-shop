"""
用户认证服务
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.auth import User, RailwayAccount
from src.utils.encryption import encrypt_password, decrypt_password
from loguru import logger


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, email: str, password: str, phone: Optional[str] = None) -> Tuple[User, str, str]:
        """
        用户注册
        返回：(用户对象，访问令牌，刷新令牌)
        """
        # 检查用户名是否已存在
        result = await self.db.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("邮箱已被注册")

        # 创建新用户
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 生成令牌
        access_token = user.create_access_token()
        refresh_token = user.create_refresh_token()

        logger.info(f"用户注册成功：{username}")
        return user, access_token, refresh_token

    async def login(self, username: str, password: str) -> Tuple[User, str, str]:
        """
        用户登录
        返回：(用户对象，访问令牌，刷新令牌)
        """
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        if not user.is_active:
            raise ValueError("用户已被禁用")

        if not user.verify_password(password):
            raise ValueError("密码错误")

        # 生成令牌
        access_token = user.create_access_token()
        refresh_token = user.create_refresh_token()

        logger.info(f"用户登录成功：{username}")
        return user, access_token, refresh_token

    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        刷新令牌
        返回：(新的访问令牌，新的刷新令牌)
        """
        payload = User.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise ValueError("用户不存在或已被禁用")

        # 生成新令牌
        new_access_token = user.create_access_token()
        new_refresh_token = user.create_refresh_token()

        return new_access_token, new_refresh_token

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_railway_account(
        self, user_id: int, railway_username: str, railway_password: str
    ) -> RailwayAccount:
        """添加 12306 账号"""
        # 加密存储 12306 密码
        encrypted_password = encrypt_password(railway_password)

        account = RailwayAccount(
            user_id=user_id,
            username=railway_username,
            password_encrypted=encrypted_password,
        )

        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)

        logger.info(f"为用户 {user_id} 添加 12306 账号：{railway_username}")
        return account

    async def get_railway_accounts(self, user_id: int) -> list:
        """获取用户的 12306 账号列表"""
        result = await self.db.execute(
            select(RailwayAccount).where(RailwayAccount.user_id == user_id)
        )
        return result.scalars().all()

    async def get_railway_account(self, account_id: int, user_id: int) -> Optional[RailwayAccount]:
        """获取 12306 账号"""
        result = await self.db.execute(
            select(RailwayAccount).where(
                RailwayAccount.id == account_id,
                RailwayAccount.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_railway_credentials(self, account_id: int) -> Optional[Tuple[str, str]]:
        """获取 12306 账号凭证（解密密码）"""
        result = await self.db.execute(
            select(RailwayAccount).where(RailwayAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            return None

        try:
            decrypted_password = decrypt_password(account.password_encrypted)
            return account.username, decrypted_password
        except Exception as e:
            logger.error(f"解密 12306 密码失败：{e}")
            return None
