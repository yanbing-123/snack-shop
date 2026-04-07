"""
订单服务测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.order_service import OrderService
from src.models.ticket import Order, OrderStatus
from src.exceptions import OrderError, InsufficientTickets


class TestOrderService:
    """订单服务测试"""

    @pytest.fixture
    def order_service(self):
        """创建订单服务实例"""
        return OrderService()

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_order_success(self, order_service, mock_db_session):
        """测试创建订单成功"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座",
            "price": 553.0
        }
        passengers = [
            {"name": "张三", "id_type": "1", "id_no": "110101199001011234"}
        ]
        
        with patch.object(order_service, '_submit_to_railway', new_callable=AsyncMock) as mock_submit:
            mock_submit.return_value = {"orderId": "E123456789", "status": "success"}
            
            order = await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=passengers
            )
            
            assert order is not None
            assert order.order_no.startswith("E")
            assert order.status == OrderStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_order_insufficient_tickets(self, order_service, mock_db_session):
        """测试余票不足"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座",
            "price": 553.0
        }
        passengers = [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        
        with patch.object(order_service, '_submit_to_railway', new_callable=AsyncMock) as mock_submit:
            mock_submit.side_effect = InsufficientTickets("余票不足")
            
            with pytest.raises(InsufficientTickets):
                await order_service.create_order(
                    db=mock_db_session,
                    user_id=1,
                    ticket_info=ticket_info,
                    passengers=passengers
                )

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, order_service, mock_db_session):
        """测试取消订单成功"""
        order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING,
            total_price=553.0
        )
        
        with patch.object(order_service, '_cancel_on_railway', new_callable=AsyncMock) as mock_cancel:
            mock_cancel.return_value = True
            
            result = await order_service.cancel_order(
                db=mock_db_session,
                order=order
            )
            
            assert result is True
            assert order.status == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_order_already_paid(self, order_service, mock_db_session):
        """测试已支付订单不能取消"""
        order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PAID,
            total_price=553.0
        )
        
        # 已支付订单不能直接取消
        result = await order_service.cancel_order(
            db=mock_db_session,
            order=order
        )
        
        assert result is False
        assert order.status == OrderStatus.PAID

    @pytest.mark.asyncio
    async def test_pay_order_success(self, order_service, mock_db_session):
        """测试支付订单成功"""
        order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING,
            total_price=553.0
        )
        
        result = await order_service.pay_order(
            db=mock_db_session,
            order=order,
            payment_method="alipay"
        )
        
        assert result is True
        assert order.status == OrderStatus.PAID
        assert order.paid_at is not None

    @pytest.mark.asyncio
    async def test_pay_order_expired(self, order_service, mock_db_session):
        """测试过期订单不能支付"""
        # 创建 30 分钟前的订单（超过支付时限）
        expired_time = datetime.now() - timedelta(minutes=30)
        order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING,
            total_price=553.0,
            created_at=expired_time
        )
        
        result = await order_service.pay_order(
            db=mock_db_session,
            order=order,
            payment_method="alipay"
        )
        
        assert result is False
        assert order.status == OrderStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, order_service, mock_db_session):
        """测试根据 ID 获取订单"""
        mock_order = Order(
            id=1,
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING
        )
        
        mock_db_session.get = AsyncMock(return_value=mock_order)
        
        order = await order_service.get_order_by_id(mock_db_session, 1)
        
        assert order is not None
        assert order.id == 1
        assert order.order_no == "E123456789"

    @pytest.mark.asyncio
    async def test_get_user_orders(self, order_service, mock_db_session):
        """测试获取用户订单列表"""
        mock_orders = [
            Order(id=1, order_no="E123456789", user_id=1, status=OrderStatus.PENDING),
            Order(id=2, order_no="E987654321", user_id=1, status=OrderStatus.PAID),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all = AsyncMock(return_value=mock_orders)
        
        mock_db_session.query.return_value = mock_query
        
        orders = await order_service.get_user_orders(mock_db_session, 1)
        
        assert len(orders) == 2
        assert all(o.user_id == 1 for o in orders)

    @pytest.mark.asyncio
    async def test_order_timeout_auto_cancel(self, order_service, mock_db_session):
        """测试订单超时自动取消"""
        # 创建超时订单
        expired_time = datetime.now() - timedelta(minutes=30)
        order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING,
            created_at=expired_time
        )
        
        # 检查订单状态
        await order_service.check_order_timeout(mock_db_session, order)
        
        assert order.status == OrderStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_duplicate_order_prevention(self, order_service, mock_db_session):
        """测试防止重复下单"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座"
        }
        passengers = [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        
        # 模拟已存在相同订单
        existing_order = Order(
            order_no="E123456789",
            user_id=1,
            status=OrderStatus.PENDING,
            train_no="G123",
            passenger_name="张三"
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first = AsyncMock(return_value=existing_order)
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(OrderError) as exc_info:
            await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=passengers
            )
        
        assert "重复" in str(exc_info.value) or "已存在" in str(exc_info.value)


class TestOrderServiceEdgeCases:
    """订单服务边界测试"""

    @pytest.fixture
    def order_service(self):
        return OrderService()

    @pytest.mark.asyncio
    async def test_empty_passengers(self, order_service, mock_db_session):
        """测试空乘客列表"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座"
        }
        
        with pytest.raises(OrderError):
            await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=[]
            )

    @pytest.mark.asyncio
    async def test_too_many_passengers(self, order_service, mock_db_session):
        """测试超过最大乘客数"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座"
        }
        # 创建超过限制的乘客列表（一单最多 5 人）
        passengers = [{"name": f"乘客{i}", "id_type": "1", "id_no": f"11010119900101123{i}"} for i in range(10)]
        
        with pytest.raises(OrderError):
            await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=passengers
            )

    @pytest.mark.asyncio
    async def test_invalid_id_number(self, order_service, mock_db_session):
        """测试无效身份证号"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座"
        }
        passengers = [{"name": "张三", "id_type": "1", "id_no": "invalid_id"}]
        
        with pytest.raises(OrderError):
            await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=passengers
            )

    @pytest.mark.asyncio
    async def test_zero_price(self, order_service, mock_db_session):
        """测试零价格订单"""
        ticket_info = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "seat_type": "二等座",
            "price": 0
        }
        passengers = [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        
        # 零价格应该被拒绝或特殊处理
        with pytest.raises(OrderError):
            await order_service.create_order(
                db=mock_db_session,
                user_id=1,
                ticket_info=ticket_info,
                passengers=passengers
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
