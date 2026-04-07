"""
车次查询 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from src.core.database import get_db
from src.services.railway_service import railway_service
from src.api.routes.auth import get_current_user
from src.models.auth import User

router = APIRouter()


class TicketQueryRequest(BaseModel):
    """余票查询请求"""
    from_station: str
    to_station: str
    travel_date: str
    train_no: Optional[str] = None


class SeatInfo(BaseModel):
    """座位信息"""
    seat_type: str
    ticket_count: str
    price: Optional[float] = None


class TrainInfo(BaseModel):
    """车次信息"""
    train_no: str
    from_station: str
    to_station: str
    from_time: str
    to_time: str
    duration: str
    seats: List[SeatInfo]


@router.get("/query", response_model=List[TrainInfo])
async def query_tickets(
    from_station: str = Query(..., description="始发站"),
    to_station: str = Query(..., description="终点站"),
    travel_date: str = Query(..., description="出行日期 (YYYY-MM-DD)"),
    train_no: Optional[str] = Query(None, description="车次号（可选）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询余票"""
    try:
        # 调用 12306 服务查询
        results = await railway_service.query_tickets(
            from_station=from_station,
            to_station=to_station,
            travel_date=travel_date,
        )

        # 过滤车次（如果指定了）
        if train_no:
            results = [r for r in results if r.get("train_no") == train_no]

        # 转换为响应格式
        response = []
        for train in results:
            seats = []
            for seat_type, count in train.get("seat_types", {}).items():
                if count and count != "":
                    seats.append(SeatInfo(
                        seat_type=seat_type,
                        ticket_count=count,
                    ))
            
            response.append(TrainInfo(
                train_no=train.get("train_no", ""),
                from_station=train.get("from_station", ""),
                to_station=train.get("to_station", ""),
                from_time=train.get("from_time", ""),
                to_time=train.get("to_time", ""),
                duration=train.get("duration", ""),
                seats=seats,
            ))

        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询失败：{str(e)}",
        )


@router.get("/stations")
async def get_stations(
    keyword: str = Query(..., description="车站关键词"),
    current_user: User = Depends(get_current_user),
):
    """搜索车站"""
    # 实际实现需要查询车站代码数据库
    # 这里提供示例数据
    stations = [
        {"name": "北京", "code": "BJP", "pinyin": "beijing"},
        {"name": "上海", "code": "SHH", "pinyin": "shanghai"},
        {"name": "广州", "code": "GZQ", "pinyin": "guangzhou"},
        {"name": "深圳", "code": "SZQ", "pinyin": "shenzhen"},
        {"name": "杭州", "code": "HZH", "pinyin": "hangzhou"},
        {"name": "南京", "code": "NJH", "pinyin": "nanjing"},
    ]
    
    # 简单过滤
    filtered = [s for s in stations if keyword.lower() in s["name"] or keyword.lower() in s["pinyin"]]
    
    return filtered
