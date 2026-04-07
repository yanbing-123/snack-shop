"""
乘车人管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.core.database import get_db
from src.api.routes.auth import get_current_user
from src.models.auth import User, Passenger

router = APIRouter()


class PassengerRequest(BaseModel):
    """乘车人请求"""
    name: str
    id_type: str = "ID_CARD"
    id_number: str
    phone: Optional[str] = None
    passenger_type: str = "ADULT"


class PassengerResponse(BaseModel):
    """乘车人响应"""
    passenger_id: int
    name: str
    id_type: str
    id_number: str
    phone: Optional[str]
    passenger_type: str
    created_at: str


@router.post("/", response_model=PassengerResponse)
async def add_passenger(
    request: PassengerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加乘车人"""
    # 检查身份证号是否已存在
    result = await db.execute(
        select(Passenger).where(
            Passenger.id_number == request.id_number,
            Passenger.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该乘车人已存在")
    
    # 创建乘车人
    passenger = Passenger(
        user_id=current_user.id,
        name=request.name,
        id_type=request.id_type,
        id_number=request.id_number,
        phone=request.phone,
        passenger_type=request.passenger_type,
    )
    
    db.add(passenger)
    await db.commit()
    await db.refresh(passenger)
    
    return PassengerResponse(
        passenger_id=passenger.id,
        name=passenger.name,
        id_type=passenger.id_type,
        id_number=passenger.id_number,
        phone=passenger.phone,
        passenger_type=passenger.passenger_type,
        created_at=passenger.created_at.isoformat(),
    )


@router.get("/", response_model=List[PassengerResponse])
async def get_passengers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取乘车人列表"""
    result = await db.execute(
        select(Passenger)
        .where(Passenger.user_id == current_user.id)
        .order_by(Passenger.created_at.desc())
    )
    passengers = result.scalars().all()
    
    return [
        PassengerResponse(
            passenger_id=p.id,
            name=p.name,
            id_type=p.id_type,
            id_number=p.id_number,
            phone=p.phone,
            passenger_type=p.passenger_type,
            created_at=p.created_at.isoformat(),
        )
        for p in passengers
    ]


@router.get("/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(
    passenger_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取乘车人详情"""
    result = await db.execute(
        select(Passenger).where(
            Passenger.id == passenger_id,
            Passenger.user_id == current_user.id,
        )
    )
    passenger = result.scalar_one_or_none()
    
    if not passenger:
        raise HTTPException(status_code=404, detail="乘车人不存在")
    
    return PassengerResponse(
        passenger_id=passenger.id,
        name=passenger.name,
        id_type=passenger.id_type,
        id_number=passenger.id_number,
        phone=passenger.phone,
        passenger_type=passenger.passenger_type,
        created_at=passenger.created_at.isoformat(),
    )


@router.put("/{passenger_id}", response_model=PassengerResponse)
async def update_passenger(
    passenger_id: int,
    request: PassengerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新乘车人信息"""
    result = await db.execute(
        select(Passenger).where(
            Passenger.id == passenger_id,
            Passenger.user_id == current_user.id,
        )
    )
    passenger = result.scalar_one_or_none()
    
    if not passenger:
        raise HTTPException(status_code=404, detail="乘车人不存在")
    
    # 更新信息
    passenger.name = request.name
    passenger.id_type = request.id_type
    passenger.id_number = request.id_number
    passenger.phone = request.phone
    passenger.passenger_type = request.passenger_type
    
    await db.commit()
    await db.refresh(passenger)
    
    return PassengerResponse(
        passenger_id=passenger.id,
        name=passenger.name,
        id_type=passenger.id_type,
        id_number=passenger.id_number,
        phone=passenger.phone,
        passenger_type=passenger.passenger_type,
        created_at=passenger.created_at.isoformat(),
    )


@router.delete("/{passenger_id}")
async def delete_passenger(
    passenger_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除乘车人"""
    result = await db.execute(
        select(Passenger).where(
            Passenger.id == passenger_id,
            Passenger.user_id == current_user.id,
        )
    )
    passenger = result.scalar_one_or_none()
    
    if not passenger:
        raise HTTPException(status_code=404, detail="乘车人不存在")
    
    await db.delete(passenger)
    await db.commit()
    
    return {"message": "乘车人已删除"}
