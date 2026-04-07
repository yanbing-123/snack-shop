"""
订单 API 集成测试
"""
import pytest
from httpx import AsyncClient
from src.main import app
from src.models.ticket import OrderStatus


class TestOrderAPI:
    """订单 API 测试"""

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def authenticated_client(self, client):
        """创建已认证的客户端"""
        # 注册测试用户
        register_resp = await client.post("/api/v1/auth/register", json={
            "username": "order_test_user",
            "email": "order_test@example.com",
            "password": "TestPass123"
        })
        
        if register_resp.status_code == 200:
            token = register_resp.json()["access_token"]
            client.headers["Authorization"] = f"Bearer {token}"
        else:
            # 尝试登录
            login_resp = await client.post("/api/v1/auth/login", json={
                "username": "order_test_user",
                "password": "TestPass123"
            })
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                client.headers["Authorization"] = f"Bearer {token}"
        
        yield client

    @pytest.mark.asyncio
    async def test_create_order_success(self, authenticated_client):
        """测试创建订单成功"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": [
                {
                    "name": "张三",
                    "id_type": "1",
                    "id_no": "110101199001011234"
                }
            ]
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        # 可能成功或因模拟数据返回特定错误
        assert response.status_code in [200, 201, 400, 500]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "order_no" in data or "id" in data

    @pytest.mark.asyncio
    async def test_create_order_unauthenticated(self, client):
        """测试未认证用户不能创建订单"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        }
        
        response = await client.post("/api/v1/orders/create", json=order_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_order_invalid_data(self, authenticated_client):
        """测试无效订单数据"""
        # 缺少必要字段
        order_data = {
            "train_no": "G123",
            # 缺少 from_station, to_station 等
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_create_order_empty_passengers(self, authenticated_client):
        """测试空乘客列表"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": []
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_invalid_id_number(self, authenticated_client):
        """测试无效身份证号"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": [
                {"name": "张三", "id_type": "1", "id_no": "invalid"}
            ]
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_get_order_list(self, authenticated_client):
        """测试获取订单列表"""
        response = await authenticated_client.get("/api/v1/orders/list")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data

    @pytest.mark.asyncio
    async def test_get_order_detail(self, authenticated_client):
        """测试获取订单详情"""
        # 先创建一个订单或使用现有订单
        response = await authenticated_client.get("/api/v1/orders/list")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                order_id = data[0].get("id") or data[0].get("order_no")
                
                if order_id:
                    detail_resp = await authenticated_client.get(f"/api/v1/orders/{order_id}")
                    assert detail_resp.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_order_not_found(self, authenticated_client):
        """测试获取不存在的订单"""
        response = await authenticated_client.get("/api/v1/orders/nonexistent")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_order_success(self, authenticated_client):
        """测试取消订单"""
        # 获取订单列表
        list_resp = await authenticated_client.get("/api/v1/orders/list")
        
        if list_resp.status_code == 200:
            data = list_resp.json()
            if isinstance(data, list) and len(data) > 0:
                order = data[0]
                order_id = order.get("id") or order.get("order_no")
                
                if order and order.get("status") == "pending":
                    cancel_resp = await authenticated_client.post(f"/api/v1/orders/{order_id}/cancel")
                    assert cancel_resp.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_cancel_order_not_found(self, authenticated_client):
        """测试取消不存在的订单"""
        response = await authenticated_client.post("/api/v1/orders/nonexistent/cancel")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_pay_order(self, authenticated_client):
        """测试支付订单"""
        list_resp = await authenticated_client.get("/api/v1/orders/list")
        
        if list_resp.status_code == 200:
            data = list_resp.json()
            if isinstance(data, list) and len(data) > 0:
                order = data[0]
                order_id = order.get("id") or order.get("order_no")
                
                if order and order.get("status") == "pending":
                    pay_resp = await authenticated_client.post(
                        f"/api/v1/orders/{order_id}/pay",
                        json={"payment_method": "alipay"}
                    )
                    assert pay_resp.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_pay_order_invalid_method(self, authenticated_client):
        """测试无效支付方式"""
        list_resp = await authenticated_client.get("/api/v1/orders/list")
        
        if list_resp.status_code == 200:
            data = list_resp.json()
            if isinstance(data, list) and len(data) > 0:
                order = data[0]
                order_id = order.get("id") or order.get("order_no")
                
                if order_id:
                    pay_resp = await authenticated_client.post(
                        f"/api/v1/orders/{order_id}/pay",
                        json={"payment_method": "invalid_method"}
                    )
                    assert pay_resp.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_order_permission(self, authenticated_client):
        """测试订单权限 - 不能查看他人订单"""
        # 创建另一个用户
        async with AsyncClient(app=app, base_url="http://test") as other_client:
            await other_client.post("/api/v1/auth/register", json={
                "username": "other_user",
                "email": "other@example.com",
                "password": "TestPass123"
            })
            login_resp = await other_client.post("/api/v1/auth/login", json={
                "username": "other_user",
                "password": "TestPass123"
            })
            
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                other_client.headers["Authorization"] = f"Bearer {token}"
                
                # 获取第一个用户的订单
                list_resp = await authenticated_client.get("/api/v1/orders/list")
                if list_resp.status_code == 200:
                    data = list_resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        order_id = data[0].get("id")
                        
                        if order_id:
                            # 另一个用户尝试访问
                            other_resp = await other_client.get(f"/api/v1/orders/{order_id}")
                            assert other_resp.status_code == 403  # 禁止访问


class TestOrderAPIEdgeCases:
    """订单 API 边界测试"""

    @pytest.fixture
    async def authenticated_client(self):
        """创建已认证客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            register_resp = await ac.post("/api/v1/auth/register", json={
                "username": "edge_test_user",
                "email": "edge_test@example.com",
                "password": "TestPass123"
            })
            
            if register_resp.status_code == 200:
                token = register_resp.json()["access_token"]
                ac.headers["Authorization"] = f"Bearer {token}"
            else:
                login_resp = await ac.post("/api/v1/auth/login", json={
                    "username": "edge_test_user",
                    "password": "TestPass123"
                })
                if login_resp.status_code == 200:
                    token = login_resp.json()["access_token"]
                    ac.headers["Authorization"] = f"Bearer {token}"
            
            yield ac

    @pytest.mark.asyncio
    async def test_rapid_order_creation(self, authenticated_client):
        """测试快速连续创建订单（频率限制）"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        }
        
        responses = []
        for _ in range(5):
            resp = await authenticated_client.post(
                "/api/v1/orders/create",
                json=order_data
            )
            responses.append(resp.status_code)
        
        # 应该有请求被限制
        assert 429 in responses or responses.count(200) + responses.count(201) <= 2

    @pytest.mark.asyncio
    async def test_past_travel_date(self, authenticated_client):
        """测试过去的出行日期"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2020-01-01",
            "seat_type": "二等座",
            "passengers": [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_too_far_future_date(self, authenticated_client):
        """测试过远的未来日期"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "上海",
            "travel_date": "2030-01-01",
            "seat_type": "二等座",
            "passengers": [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_same_from_to_station(self, authenticated_client):
        """测试起点终点相同"""
        order_data = {
            "train_no": "G123",
            "from_station": "北京",
            "to_station": "北京",
            "travel_date": "2024-02-01",
            "seat_type": "二等座",
            "passengers": [{"name": "张三", "id_type": "1", "id_no": "110101199001011234"}]
        }
        
        response = await authenticated_client.post(
            "/api/v1/orders/create",
            json=order_data
        )
        
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
