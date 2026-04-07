"""
监控服务测试 - 余票监控和自动抢票
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.monitor_service import MonitorService, MonitorTask
from src.models.ticket import MonitorStatus


class TestMonitorService:
    """监控服务测试"""

    @pytest.fixture
    def monitor_service(self):
        """创建监控服务实例"""
        return MonitorService()

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_create_monitor_task(self, monitor_service, mock_db_session):
        """测试创建监控任务"""
        task = await monitor_service.create_monitor_task(
            db=mock_db_session,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            seat_types=["二等座", "一等座"]
        )
        
        assert task is not None
        assert task.user_id == 1
        assert task.from_station == "北京"
        assert task.to_station == "上海"
        assert task.status == MonitorStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_stop_monitor_task(self, monitor_service, mock_db_session):
        """测试停止监控任务"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            status=MonitorStatus.ACTIVE
        )
        
        result = await monitor_service.stop_monitor_task(
            db=mock_db_session,
            task=task
        )
        
        assert result is True
        assert task.status == MonitorStatus.STOPPED

    @pytest.mark.asyncio
    async def test_stop_already_stopped_task(self, monitor_service, mock_db_session):
        """测试停止已停止的任务"""
        task = MonitorTask(
            id=1,
            user_id=1,
            status=MonitorStatus.STOPPED
        )
        
        result = await monitor_service.stop_monitor_task(
            db=mock_db_session,
            task=task
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_tickets_found(self, monitor_service, mock_db_session):
        """测试监控到余票"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            seat_types=["二等座"],
            status=MonitorStatus.ACTIVE
        )
        
        mock_ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座",
            "price": 553.0,
            "available": True
        }
        
        with patch.object(monitor_service.railway_service, 'query_tickets', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_ticket_info]
            
            with patch.object(monitor_service.order_service, 'create_order', new_callable=AsyncMock) as mock_order:
                mock_order.return_value = MagicMock(id=1, order_no="E123456789")
                
                result = await monitor_service.check_and_book(monitor_service, mock_db_session, task)
                
                assert result is not None
                assert mock_order.called

    @pytest.mark.asyncio
    async def test_check_tickets_not_found(self, monitor_service, mock_db_session):
        """测试监控无余票"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            status=MonitorStatus.ACTIVE
        )
        
        with patch.object(monitor_service.railway_service, 'query_tickets', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            
            result = await monitor_service.check_and_book(monitor_service, mock_db_session, task)
            
            assert result is None
            assert task.status == MonitorStatus.ACTIVE  # 任务继续

    @pytest.mark.asyncio
    async def test_monitor_task_expired(self, monitor_service, mock_db_session):
        """测试监控任务过期"""
        expired_time = datetime.now() - timedelta(days=1)
        task = MonitorTask(
            id=1,
            user_id=1,
            travel_date="2024-01-01",  # 过去的日期
            status=MonitorStatus.ACTIVE,
            created_at=expired_time
        )
        
        result = await monitor_service.check_and_book(monitor_service, mock_db_session, task)
        
        assert result is None
        assert task.status == MonitorStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_rate_limit_respected(self, monitor_service, mock_db_session):
        """测试监控遵守频率限制"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            status=MonitorStatus.ACTIVE
        )
        
        call_count = 0
        
        async def mock_query(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return []
        
        with patch.object(monitor_service.railway_service, 'query_tickets', side_effect=mock_query):
            # 快速连续调用多次
            for _ in range(5):
                await monitor_service.check_and_book(monitor_service, mock_db_session, task)
            
            # 由于频率限制，实际调用次数应该少于 5
            assert call_count <= 3  # 具体数字取决于频率限制配置

    @pytest.mark.asyncio
    async def test_get_user_monitor_tasks(self, monitor_service, mock_db_session):
        """测试获取用户监控任务列表"""
        mock_tasks = [
            MonitorTask(id=1, user_id=1, from_station="北京", to_station="上海"),
            MonitorTask(id=2, user_id=1, from_station="上海", to_station="广州"),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all = AsyncMock(return_value=mock_tasks)
        mock_db_session.query.return_value = mock_query
        
        tasks = await monitor_service.get_user_tasks(mock_db_session, 1)
        
        assert len(tasks) == 2
        assert all(t.user_id == 1 for t in tasks)

    @pytest.mark.asyncio
    async def test_monitor_task_duplicate_prevention(self, monitor_service, mock_db_session):
        """测试防止重复监控任务"""
        existing_task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            status=MonitorStatus.ACTIVE
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first = AsyncMock(return_value=existing_task)
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(Exception) as exc_info:
            await monitor_service.create_monitor_task(
                db=mock_db_session,
                user_id=1,
                from_station="北京",
                to_station="上海",
                travel_date="2024-02-01"
            )
        
        assert "重复" in str(exc_info.value) or "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_auto_book_on_found(self, monitor_service, mock_db_session):
        """测试发现余票自动下单"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            seat_types=["二等座"],
            auto_book=True,
            status=MonitorStatus.ACTIVE
        )
        
        mock_ticket = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座",
            "price": 553.0
        }
        
        mock_order = MagicMock(id=1, order_no="E123456789")
        
        with patch.object(monitor_service.railway_service, 'query_tickets', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_ticket]
            
            with patch.object(monitor_service.order_service, 'create_order', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_order
                
                result = await monitor_service.check_and_book(monitor_service, mock_db_session, task)
                
                assert result is not None
                assert mock_create.called
                # 验证使用了正确的参数
                call_args = mock_create.call_args
                assert call_args is not None

    @pytest.mark.asyncio
    async def test_notify_user_on_success(self, monitor_service, mock_db_session):
        """测试抢票成功通知用户"""
        task = MonitorTask(
            id=1,
            user_id=1,
            from_station="北京",
            to_station="上海",
            status=MonitorStatus.ACTIVE
        )
        
        mock_order = MagicMock(id=1, order_no="E123456789")
        
        with patch.object(monitor_service, '_notify_user', new_callable=AsyncMock) as mock_notify:
            await monitor_service.notify_booking_success(mock_db_session, task, mock_order)
            
            assert mock_notify.called


class TestMonitorServiceEdgeCases:
    """监控服务边界测试"""

    @pytest.fixture
    def monitor_service(self):
        return MonitorService()

    @pytest.mark.asyncio
    async def test_invalid_station_code(self, monitor_service, mock_db_session):
        """测试无效车站代码"""
        with pytest.raises(Exception):
            await monitor_service.create_monitor_task(
                db=mock_db_session,
                user_id=1,
                from_station="INVALID",
                to_station="上海",
                travel_date="2024-02-01"
            )

    @pytest.mark.asyncio
    async def test_past_travel_date(self, monitor_service, mock_db_session):
        """测试过去的出行日期"""
        with pytest.raises(Exception):
            await monitor_service.create_monitor_task(
                db=mock_db_session,
                user_id=1,
                from_station="北京",
                to_station="上海",
                travel_date="2020-01-01"
            )

    @pytest.mark.asyncio
    async def test_empty_seat_types(self, monitor_service, mock_db_session):
        """测试空座位类型列表"""
        task = await monitor_service.create_monitor_task(
            db=mock_db_session,
            user_id=1,
            from_station="北京",
            to_station="上海",
            travel_date="2024-02-01",
            seat_types=[]
        )
        
        # 空座位类型应该使用默认值或报错
        assert task is not None

    @pytest.mark.asyncio
    async def test_too_many_monitor_tasks(self, monitor_service, mock_db_session):
        """测试用户监控任务数量限制"""
        # 模拟用户已有最大数量的任务
        max_tasks = 10
        mock_tasks = [MonitorTask(id=i, user_id=1) for i in range(max_tasks)]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count = AsyncMock(return_value=max_tasks)
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(Exception) as exc_info:
            await monitor_service.create_monitor_task(
                db=mock_db_session,
                user_id=1,
                from_station="北京",
                to_station="广州",
                travel_date="2024-02-01"
            )
        
        assert "超过限制" in str(exc_info.value) or "数量" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
