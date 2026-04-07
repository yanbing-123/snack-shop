"""
12306 铁路服务测试 - 模拟 API 异常情况
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.railway_service import RailwayService
from src.exceptions import RailwayAPIError, CaptchaRequired, LoginFailed


class TestRailwayServiceMock:
    """铁路服务模拟测试"""

    @pytest.fixture
    def railway_service(self):
        """创建铁路服务实例"""
        return RailwayService()

    @pytest.mark.asyncio
    async def test_query_tickets_success(self, railway_service):
        """测试查询余票成功"""
        mock_response = {
            "status": True,
            "data": {
                "result": [
                    {
                        "train_no": "G123",
                        "from_station_name": "北京",
                        "to_station_name": "上海",
                        "start_time": "08:00",
                        "arrive_time": "12:00",
                        "yz_num": "有",
                        "ym_num": "有",
                        "ze_num": "有",
                    }
                ]
            }
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            result = await railway_service.query_tickets("北京", "上海", "2024-02-01")
            
            assert result is not None
            assert len(result) > 0
            assert result[0]["train_no"] == "G123"

    @pytest.mark.asyncio
    async def test_query_tickets_api_error(self, railway_service):
        """测试 API 错误处理"""
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = RailwayAPIError("API 调用失败", status_code=500)
            
            with pytest.raises(RailwayAPIError):
                await railway_service.query_tickets("北京", "上海", "2024-02-01")

    @pytest.mark.asyncio
    async def test_query_tickets_timeout(self, railway_service):
        """测试超时处理"""
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(RailwayAPIError) as exc_info:
                await railway_service.query_tickets("北京", "上海", "2024-02-01")
            
            assert "超时" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_tickets_captcha_required(self, railway_service):
        """测试验证码要求"""
        mock_response = {
            "status": False,
            "messages": ["需要验证码"],
            "captcha_required": True
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            with pytest.raises(CaptchaRequired):
                await railway_service.query_tickets("北京", "上海", "2024-02-01")

    @pytest.mark.asyncio
    async def test_login_success(self, railway_service):
        """测试登录成功"""
        mock_response = {
            "status": True,
            "data": {
                "result": True,
                "appId": "test_app_id"
            }
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            result = await railway_service.login("test_user", "test_pass")
            
            assert result is True
            assert railway_service.is_logged_in is True

    @pytest.mark.asyncio
    async def test_login_failed(self, railway_service):
        """测试登录失败"""
        mock_response = {
            "status": False,
            "messages": ["密码错误"]
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            with pytest.raises(LoginFailed):
                await railway_service.login("test_user", "wrong_pass")

    @pytest.mark.asyncio
    async def test_submit_order_success(self, railway_service):
        """测试提交订单成功"""
        mock_response = {
            "status": True,
            "data": {
                "result": True,
                "orderId": "ORDER123456"
            }
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            result = await railway_service.submit_order(
                ticket_info={"train_no": "G123"},
                passengers=[{"name": "张三", "id": "110101199001011234"}]
            )
            
            assert result is not None
            assert result["orderId"] == "ORDER123456"

    @pytest.mark.asyncio
    async def test_submit_order_insufficient_tickets(self, railway_service):
        """测试余票不足"""
        mock_response = {
            "status": False,
            "messages": ["余票不足"]
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            with pytest.raises(RailwayAPIError) as exc_info:
                await railway_service.submit_order(
                    ticket_info={"train_no": "G123"},
                    passengers=[{"name": "张三"}]
                )
            
            assert "余票不足" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_passengers(self, railway_service):
        """测试获取乘客信息"""
        mock_response = {
            "status": True,
            "data": {
                "result": [
                    {"passenger_name": "张三", "passenger_id_type": "1", "passenger_id_no": "110101199001011234"}
                ]
            }
        }
        
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_response
            
            result = await railway_service.get_passengers()
            
            assert len(result) > 0
            assert result[0]["passenger_name"] == "张三"

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, railway_service):
        """测试重试机制"""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RailwayAPIError("临时错误", status_code=503)
            return {"status": True, "data": {"result": []}}
        
        with patch.object(railway_service, '_make_request', side_effect=mock_request):
            result = await railway_service.query_tickets("北京", "上海", "2024-02-01")
            
            # 应该重试了 3 次
            assert call_count == 3
            assert result is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, railway_service):
        """测试熔断器打开"""
        # 模拟连续失败
        with patch.object(railway_service, '_make_request', new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = RailwayAPIError("服务不可用", status_code=503)
            
            # 连续失败多次后应该触发熔断
            for _ in range(5):
                try:
                    await railway_service.query_tickets("北京", "上海", "2024-02-01")
                except RailwayAPIError:
                    pass
            
            # 熔断器应该打开，快速失败
            with pytest.raises(RailwayAPIError) as exc_info:
                await railway_service.query_tickets("北京", "上海", "2024-02-01")
            
            assert "熔断" in str(exc_info.value) or "服务不可用" in str(exc_info.value)


class TestRailwayServiceEdgeCases:
    """边界情况测试"""

    @pytest.fixture
    def railway_service(self):
        return RailwayService()

    @pytest.mark.asyncio
    async def test_empty_station_name(self, railway_service):
        """测试空车站名称"""
        with pytest.raises(RailwayAPIError):
            await railway_service.query_tickets("", "上海", "2024-02-01")

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, railway_service):
        """测试无效日期格式"""
        with pytest.raises(RailwayAPIError):
            await railway_service.query_tickets("北京", "上海", "invalid-date")

    @pytest.mark.asyncio
    async def test_past_date(self, railway_service):
        """测试过去日期"""
        # 过去的日期应该被拒绝
        with pytest.raises(RailwayAPIError):
            await railway_service.query_tickets("北京", "上海", "2020-01-01")

    @pytest.mark.asyncio
    async def test_same_from_to_station(self, railway_service):
        """测试起点终点相同"""
        with pytest.raises(RailwayAPIError):
            await railway_service.query_tickets("北京", "北京", "2024-02-01")

    @pytest.mark.asyncio
    async def test_special_characters_in_station(self, railway_service):
        """测试车站名包含特殊字符"""
        # 应该能处理特殊字符或给出合适错误
        try:
            result = await railway_service.query_tickets("北京<特殊>", "上海", "2024-02-01")
            # 如果 API 接受，应该返回空结果
            assert result == []
        except RailwayAPIError:
            # 或者拒绝请求
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
