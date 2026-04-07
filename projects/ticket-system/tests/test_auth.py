"""
认证模块测试
"""
import pytest
from httpx import AsyncClient
from src.main import app
from src.core.database import database, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from src.models.auth import User

# 测试数据库配置
TEST_DATABASE_URL = "postgresql+asyncpg://test:test123@localhost:5432/ticket_system_test"


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """创建数据库会话"""
    async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session):
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    """测试用户注册"""
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "phone": "13800138000",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["username"] == "testuser"
    
    # 验证用户已保存到数据库
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_username(client, db_session):
    """测试重复用户名注册"""
    # 先创建一个用户
    await client.post("/api/v1/auth/register", json={
        "username": "duplicate_user",
        "email": "dup1@example.com",
        "password": "TestPass123",
    })
    
    # 尝试用相同用户名注册
    response = await client.post("/api/v1/auth/register", json={
        "username": "duplicate_user",
        "email": "dup2@example.com",
        "password": "TestPass123",
    })
    
    assert response.status_code == 400
    assert "用户名已存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login(client, db_session):
    """测试用户登录"""
    # 先注册用户
    await client.post("/api/v1/auth/register", json={
        "username": "login_user",
        "email": "login@example.com",
        "password": "TestPass123",
    })
    
    # 测试登录
    response = await client.post("/api/v1/auth/login", json={
        "username": "login_user",
        "password": "TestPass123",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["username"] == "login_user"


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session):
    """测试错误密码登录"""
    # 先注册用户
    await client.post("/api/v1/auth/register", json={
        "username": "wrong_pass_user",
        "email": "wrong@example.com",
        "password": "TestPass123",
    })
    
    # 测试错误密码
    response = await client.post("/api/v1/auth/login", json={
        "username": "wrong_pass_user",
        "password": "WrongPassword",
    })
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client, db_session):
    """测试获取当前用户信息"""
    # 注册并登录
    register_resp = await client.post("/api/v1/auth/register", json={
        "username": "me_user",
        "email": "me@example.com",
        "password": "TestPass123",
    })
    
    token = register_resp.json()["access_token"]
    
    # 获取用户信息
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_refresh_token(client, db_session):
    """测试刷新令牌"""
    # 注册获取令牌
    register_resp = await client.post("/api/v1/auth/register", json={
        "username": "refresh_user",
        "email": "refresh@example.com",
        "password": "TestPass123",
    })
    
    refresh_token = register_resp.json()["refresh_token"]
    
    # 刷新令牌
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["username"] == "refresh_user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
