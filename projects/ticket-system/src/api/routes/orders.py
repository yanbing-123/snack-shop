"""
订单管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.core.database import get_db
from src.api.routes.auth import get_current_user
from src.models.auth import User
from src.models.ticket import Order

router = APIRouter()


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: int
    order_no: str
    train_no: str
    from_station: str
    to_station: str
    travel_date: str
    seat_type: str
    price: float
    passengers: list
    status: str
    payment_status: str
    created_at: str
    paid_at: Optional[str]


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    railway_account_id: int
    train_no: str
    from_station: str
    to_station: str
    travel_date: str
    seat_type: str
    price: float
    passenger_ids: List[int]


@router.post("/", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建订单（自动抢票）"""
    try:
        # 生成订单号
        order_no = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        # 获取乘车人信息（简化实现）
        passengers = [{"id": pid} for pid in request.passenger_ids]
        
        # 创建订单记录
        order = Order(
            order_no=order_no,
            user_id=current_user.id,
            railway_account_id=request.railway_account_id,
            train_no=request.train_no,
            from_station=request.from_station,
            to_station=request.to_station,
            travel_date=datetime.strptime(request.travel_date, "%Y-%m-%d"),
            seat_type=request.seat_type,
            price=request.price,
            passengers=passengers,
            status="PENDING",
            payment_status="UNPAID",
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        # TODO: 调用 12306 API 提交订单
        # 这里应该调用 railway_service.submit_order()
        
        return OrderResponse(
            order_id=order.id,
            order_no=order.order_no,
            train_no=order.train_no,
            from_station=order.from_station,
            to_station=order.to_station,
            travel_date=order.travel_date.strftime("%Y-%m-%d"),
            seat_type=order.seat_type,
            price=order.price,
            passengers=order.passengers,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at.isoformat(),
            paid_at=None,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"创建订单失败：{str(e)}",
        )


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订单列表"""
    query = select(Order).where(Order.user_id == current_user.id)
    
    if status:
        query = query.where(Order.status == status)
    
    query = query.order_by(Order.created_at.desc())
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return [
        OrderResponse(
            order_id=order.id,
            order_no=order.order_no,
            train_no=order.train_no,
            from_station=order.from_station,
            to_station=order.to_station,
            travel_date=order.travel_date.strftime("%Y-%m-%d"),
            seat_type=order.seat_type,
            price=order.price,
            passengers=order.passengers,
            status=order.status,
            payment_status=order.payment_status,
            created_at=order.created_at.isoformat(),
            paid_at=order.paid_at.isoformat() if order.paid_at else None,
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取订单详情"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return OrderResponse(
        order_id=order.id,
        order_no=order.order_no,
        train_no=order.train_no,
        from_station=order.from_station,
        to_station=order.to_station,
        travel_date=order.travel_date.strftime("%Y-%m-%d"),
        seat_type=order.seat_type,
        price=order.price,
        passengers=order.passengers,
        status=order.status,
        payment_status=order.payment_status,
        created_at=order.created_at.isoformat(),
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
    )


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取消订单"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status not in ["PENDING", "SUCCESS"]:
        raise HTTPException(status_code=400, detail="订单状态不允许取消")
    
    # TODO: 调用 12306 API 取消订单
    # railway_service.cancel_order(order.railway_order_no)
    
    order.status = "CANCELLED"
    order.cancelled_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "订单已取消"}


@router.post("/{order_id}/refund")
async def refund_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """退票"""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status != "SUCCESS" or order.payment_status != "PAID":
        raise HTTPException(status_code=400, detail="订单状态不允许退票")
    
    # TODO: 调用 12306 API 退票
    # railway_service.refund_order(order.railway_order_no)
    
    order.status = "REFUNDED"
    order.payment_status = "REFUNDED"
    order.cancelled_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "退票成功"}
