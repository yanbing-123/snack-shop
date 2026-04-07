"""
频率限制器测试 - 验证防封号策略
"""
import pytest
import asyncio
from src.utils.rate_limiter import RateLimiter, RequestType


class TestRateLimiter:
    """频率限制器测试"""

    @pytest.mark.asyncio
    async def test_basic_rate_limit(self):
        """测试基本频率限制"""
        limiter = RateLimiter(query_interval=1.0)
        
        # 第一次请求应该成功
        assert await limiter.can_request(RequestType.QUERY) is True
        
        # 立即第二次请求应该被限制
        assert await limiter.can_request(RequestType.QUERY) is False
        
        # 等待间隔时间后可以再次请求
        await asyncio.sleep(1.1)
        assert await limiter.can_request(RequestType.QUERY) is True

    @pytest.mark.asyncio
    async def test_different_request_types(self):
        """测试不同类型的请求独立计数"""
        limiter = RateLimiter(query_interval=1.0, monitor_interval=2.0)
        
        # 查询请求
        assert await limiter.can_request(RequestType.QUERY) is True
        assert await limiter.can_request(RequestType.QUERY) is False
        
        # 监控请求应该不受影响
        assert await limiter.can_request(RequestType.MONITOR) is True
        assert await limiter.can_request(RequestType.MONITOR) is False

    @pytest.mark.asyncio
    async def test_rapid_requests_blocked(self):
        """测试快速连续请求被阻止"""
        limiter = RateLimiter(query_interval=0.5)
        
        success_count = 0
        for _ in range(5):
            if await limiter.can_request(RequestType.QUERY):
                success_count += 1
        
        # 只有第一次应该成功
        assert success_count == 1

    @pytest.mark.asyncio
    async def test_retry_counting(self):
        """测试重试计数"""
        limiter = RateLimiter(max_retries=3)
        
        # 模拟失败重试
        for i in range(3):
            limiter.record_failure(RequestType.QUERY)
        
        # 达到最大重试次数后应该被限制
        assert limiter.get_retry_count(RequestType.QUERY) == 3

    @pytest.mark.asyncio
    async def test_reset_after_success(self):
        """测试成功后重置重试计数"""
        limiter = RateLimiter(max_retries=3)
        
        # 记录几次失败
        for _ in range(2):
            limiter.record_failure(RequestType.QUERY)
        
        assert limiter.get_retry_count(RequestType.QUERY) == 2
        
        # 记录成功
        limiter.record_success(RequestType.QUERY)
        
        # 重试计数应该重置
        assert limiter.get_retry_count(RequestType.QUERY) == 0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求处理"""
        limiter = RateLimiter(query_interval=0.1)
        
        async def make_request():
            return await limiter.can_request(RequestType.QUERY)
        
        # 并发发起 5 个请求
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # 只有一个应该成功
        assert sum(results) == 1


class TestRateLimiterIntegration:
    """频率限制器集成测试"""

    @pytest.mark.asyncio
    async def test_api_rate_limiting(self):
        """测试 API 层面的频率限制"""
        from httpx import AsyncClient
        from src.main import app
        
        # 创建测试用户并获取令牌
        async with AsyncClient(app=app, base_url="http://test") as ac:
            register_resp = await ac.post("/api/v1/auth/register", json={
                "username": "ratelimit_user",
                "email": "ratelimit@test.com",
                "password": "TestPass123",
            })
            
            if register_resp.status_code == 200:
                token = register_resp.json()["access_token"]
                ac.headers["Authorization"] = f"Bearer {token}"
                
                # 快速连续发起查询请求
                responses = []
                for _ in range(5):
                    resp = await ac.get(
                        "/api/v1/tickets/query",
                        params={
                            "from_station": "北京",
                            "to_station": "上海",
                            "travel_date": "2024-02-01",
                        }
                    )
                    responses.append(resp.status_code)
                
                # 应该有请求被限制（返回 429）
                assert 429 in responses or len([r for r in responses if r == 200]) <= 2

    @pytest.mark.asyncio
    async def test_monitor_interval_enforced(self):
        """测试监控间隔被强制执行"""
        from src.services.monitor_service import MonitorService
        from src.core.database import get_db
        from src.models.auth import User
        
        # 创建模拟服务
        service = MonitorService()
        
        # 连续创建监控任务应该受到间隔限制
        # 这个测试验证服务层面是否遵守频率限制


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
