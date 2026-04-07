"""
Pytest 配置文件
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.database import Base, get_db
from src.main import app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


# 测试数据库 URL（使用 SQLite 内存数据库）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine):
    """创建测试数据库会话"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话（用于不需要真实数据库的测试）"""
    session = MagicMock(spec=AsyncSession)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = MagicMock()
    session.get = AsyncMock(return_value=None)
    
    mock_query = MagicMock()
    mock_query.filter = MagicMock(return_value=mock_query)
    mock_query.filter_by = MagicMock(return_value=mock_query)
    mock_query.order_by = MagicMock(return_value=mock_query)
    mock_query.first = AsyncMock(return_value=None)
    mock_query.all = AsyncMock(return_value=[])
    mock_query.count = AsyncMock(return_value=0)
    mock_query.one_or_none = AsyncMock(return_value=None)
    
    session.query = MagicMock(return_value=mock_query)
    
    return session


@pytest.fixture
def mock_railway_service():
    """创建模拟铁路服务"""
    with patch('src.services.railway_service.RailwayService') as mock:
        service = MagicMock()
        service.query_tickets = AsyncMock(return_value=[])
        service.login = AsyncMock(return_value=True)
        service.submit_order = AsyncMock(return_value={"orderId": "TEST123"})
        service.get_passengers = AsyncMock(return_value=[])
        
        mock.return_value = service
        yield service


@pytest.fixture
def mock_order_service():
    """创建模拟订单服务"""
    with patch('src.services.order_service.OrderService') as mock:
        service = MagicMock()
        service.create_order = AsyncMock(return_value=MagicMock(id=1, order_no="E123456789"))
        service.cancel_order = AsyncMock(return_value=True)
        service.pay_order = AsyncMock(return_value=True)
        service.get_order_by_id = AsyncMock(return_value=None)
        service.get_user_orders = AsyncMock(return_value=[])
        
        mock.return_value = service
        yield service


@pytest.fixture
def mock_monitor_service():
    """创建模拟监控服务"""
    with patch('src.services.monitor_service.MonitorService') as mock:
        service = MagicMock()
        service.create_monitor_task = AsyncMock(return_value=MagicMock(id=1))
        service.stop_monitor_task = AsyncMock(return_value=True)
        service.get_user_tasks = AsyncMock(return_value=[])
        service.check_and_book = AsyncMock(return_value=None)
        
        mock.return_value = service
        yield service


@pytest.fixture
def mock_rate_limiter():
    """创建模拟频率限制器"""
    with patch('src.utils.rate_limiter.RateLimiter') as mock:
        limiter = MagicMock()
        limiter.can_request = AsyncMock(return_value=True)
        limiter.record_success = MagicMock()
        limiter.record_failure = MagicMock()
        
        mock.return_value = limiter
        yield limiter


@pytest.fixture
def sample_user():
    """创建示例用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True
    }


@pytest.fixture
def sample_ticket():
    """创建示例车票数据"""
    return {
        "train_no": "G123",
        "from_station": "北京",
        "to_station": "上海",
        "travel_date": "2024-02-01",
        "seat_type": "二等座",
        "price": 553.0
    }


@pytest.fixture
def sample_passenger():
    """创建示例乘客数据"""
    return {
        "name": "张三",
        "id_type": "1",
        "id_no": "110101199001011234"
    }


@pytest.fixture
def sample_order():
    """创建示例订单数据"""
    return {
        "order_no": "E123456789",
        "user_id": 1,
        "train_no": "G123",
        "from_station": "北京",
        "to_station": "上海",
        "travel_date": "2024-02-01",
        "seat_type": "二等座",
        "total_price": 553.0,
        "status": "pending"
    }


# 自动应用某些 mock
@pytest.fixture(autouse=True)
def auto_mock_external_services(mock_railway_service, mock_rate_limiter):
    """自动模拟外部服务"""
    yield
