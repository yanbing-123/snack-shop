"""
认证服务单元测试
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.auth_service import AuthService
from src.exceptions import AuthenticationError, UserAlreadyExists


class TestAuthService:
    """认证服务测试"""

    @pytest.fixture
    def auth_service(self):
        """创建认证服务实例"""
        return AuthService()

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_db_session):
        """测试用户注册成功"""
        mock_db_session.get = AsyncMock(return_value=None)  # 用户不存在
        
        user = await auth_service.register(
            db=mock_db_session,
            username="testuser",
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password is not None
        assert user.hashed_password != "SecurePass123"  # 密码已哈希

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, mock_db_session):
        """测试重复用户名"""
        existing_user = MagicMock()
        existing_user.username = "testuser"
        mock_db_session.get = AsyncMock(return_value=existing_user)
        
        with pytest.raises(UserAlreadyExists):
            await auth_service.register(
                db=mock_db_session,
                username="testuser",
                email="other@example.com",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, mock_db_session):
        """测试重复邮箱"""
        # 模拟邮箱已存在
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first = AsyncMock(return_value=MagicMock())
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(UserAlreadyExists):
            await auth_service.register(
                db=mock_db_session,
                username="newuser",
                email="existing@example.com",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_db_session):
        """测试登录成功"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.hashed_password = pwd_context.hash("SecurePass123")
        mock_user.is_active = True
        
        mock_db_session.get = AsyncMock(return_value=mock_user)
        
        user = await auth_service.login(
            db=mock_db_session,
            username="testuser",
            password="SecurePass123"
        )
        
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, mock_db_session):
        """测试密码错误"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.hashed_password = pwd_context.hash("CorrectPass123")
        mock_user.is_active = True
        
        mock_db_session.get = AsyncMock(return_value=mock_user)
        
        with pytest.raises(AuthenticationError):
            await auth_service.login(
                db=mock_db_session,
                username="testuser",
                password="WrongPass123"
            )

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, auth_service, mock_db_session):
        """测试用户不存在"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        with pytest.raises(AuthenticationError):
            await auth_service.login(
                db=mock_db_session,
                username="nonexistent",
                password="AnyPass123"
            )

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, auth_service, mock_db_session):
        """测试未激活用户"""
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.hashed_password = "hashed"
        mock_user.is_active = False
        
        mock_db_session.get = AsyncMock(return_value=mock_user)
        
        with pytest.raises(AuthenticationError):
            await auth_service.login(
                db=mock_db_session,
                username="testuser",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service):
        """测试创建访问令牌"""
        from datetime import timedelta
        
        token = await auth_service.create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT 令牌应该足够长

    @pytest.mark.asyncio
    async def test_verify_token_success(self, auth_service):
        """测试验证令牌成功"""
        from datetime import timedelta
        
        token = await auth_service.create_access_token(
            data={"sub": "testuser", "user_id": 1},
            expires_delta=timedelta(minutes=30)
        )
        
        payload = await auth_service.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == 1

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, auth_service):
        """测试过期令牌"""
        from datetime import timedelta
        
        token = await auth_service.create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        
        with pytest.raises(Exception):
            await auth_service.verify_token(token)

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """测试无效令牌"""
        with pytest.raises(Exception):
            await auth_service.verify_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_password_hashing(self, auth_service):
        """测试密码哈希"""
        password = "SecurePass123"
        
        hashed1 = auth_service._hash_password(password)
        hashed2 = auth_service._hash_password(password)
        
        # 两次哈希结果应该不同（盐值不同）
        assert hashed1 != hashed2
        
        # 但验证都应该通过
        assert auth_service._verify_password(password, hashed1)
        assert auth_service._verify_password(password, hashed2)

    @pytest.mark.asyncio
    async def test_weak_password_rejected(self, auth_service, mock_db_session):
        """测试弱密码被拒绝"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        # 太短的密码
        with pytest.raises(Exception):
            await auth_service.register(
                db=mock_db_session,
                username="testuser",
                email="test@example.com",
                password="123"
            )

    @pytest.mark.asyncio
    async def test_invalid_email_format(self, auth_service, mock_db_session):
        """测试无效邮箱格式"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        with pytest.raises(Exception):
            await auth_service.register(
                db=mock_db_session,
                username="testuser",
                email="invalid-email",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service, mock_db_session):
        """测试根据 ID 获取用户"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        
        mock_db_session.get = AsyncMock(return_value=mock_user)
        
        user = await auth_service.get_user_by_id(mock_db_session, 1)
        
        assert user is not None
        assert user.id == 1

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, auth_service, mock_db_session):
        """测试根据邮箱获取用户"""
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first = AsyncMock(return_value=mock_user)
        mock_db_session.query.return_value = mock_query
        
        user = await auth_service.get_user_by_email(mock_db_session, "test@example.com")
        
        assert user is not None
        assert user.email == "test@example.com"


class TestAuthServiceEdgeCases:
    """认证服务边界测试"""

    @pytest.fixture
    def auth_service(self):
        return AuthService()

    @pytest.mark.asyncio
    async def test_username_with_special_chars(self, auth_service, mock_db_session):
        """测试包含特殊字符的用户名"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        # 某些特殊字符应该被拒绝
        with pytest.raises(Exception):
            await auth_service.register(
                db=mock_db_session,
                username="user<script>",
                email="test@example.com",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_very_long_username(self, auth_service, mock_db_session):
        """测试超长用户名"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        with pytest.raises(Exception):
            await auth_service.register(
                db=mock_db_session,
                username="a" * 100,
                email="test@example.com",
                password="SecurePass123"
            )

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, auth_service, mock_db_session):
        """测试 SQL 注入尝试"""
        mock_db_session.get = AsyncMock(return_value=None)
        
        # 应该被参数化查询阻止
        try:
            await auth_service.login(
                db=mock_db_session,
                username="admin' OR '1'='1",
                password="anything"
            )
        except AuthenticationError:
            # 正确的行为 - 认证失败而不是 SQL 错误
            pass

    @pytest.mark.asyncio
    async def test_concurrent_registrations(self, auth_service, mock_db_session):
        """测试并发注册"""
        import asyncio
        
        mock_db_session.get = AsyncMock(return_value=None)
        
        async def register_user(username):
            try:
                return await auth_service.register(
                    db=mock_db_session,
                    username=username,
                    email=f"{username}@example.com",
                    password="SecurePass123"
                )
            except UserAlreadyExists:
                return None
        
        # 并发注册相同用户名的用户
        results = await asyncio.gather(
            register_user("concurrent_user"),
            register_user("concurrent_user"),
            register_user("concurrent_user")
        )
        
        # 只有一个应该成功
        success_count = sum(1 for r in results if r is not None)
        assert success_count <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
