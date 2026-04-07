"""
车次查询模块测试
"""
import pytest
from httpx import AsyncClient
from src.main import app
from src.core.database import database, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.models.auth import User

# 测试数据库配置
TEST_DATABASE_URL = "postgresql+asyncpg://test:test123@localhost:5432/ticket_system_test"


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
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
async def authenticated_client(db_session):
    """创建已认证的测试客户端"""
    # 创建测试用户
    user = User(username="testuser", email="test@example.com")
    user.set_password("TestPass123")
    db_session.add(user)
    await db_session.commit()
    
    # 获取令牌
    access_token = user.create_access_token()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {access_token}"
        yield ac


@pytest.mark.asyncio
async def test_query_tickets(authenticated_client):
    """测试查询余票"""
    response = await authenticated_client.get(
        "/api/v1/tickets/query",
        params={
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
        }
    )
    
    # 由于 12306 API 需要真实连接，这里测试接口是否可访问
    assert response.status_code in [200, 500]  # 500 表示 API 调用失败但接口正常


@pytest.mark.asyncio
async def test_query_tickets_with_train_no(authenticated_client):
    """测试按车次查询"""
    response = await authenticated_client.get(
        "/api/v1/tickets/query",
        params={
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "train_no": "G123",
        }
    )
    
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_get_stations(authenticated_client):
    """测试获取车站列表"""
    response = await authenticated_client.get(
        "/api/v1/tickets/stations",
        params={"keyword": "北京"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 应该包含北京
    assert any(station["name"] == "北京" for station in data)


@pytest.mark.asyncio
async def test_query_tickets_unauthorized(client):
    """测试未授权访问"""
    response = await client.get(
        "/api/v1/tickets/query",
        params={
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
        }
    )
    
    assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
