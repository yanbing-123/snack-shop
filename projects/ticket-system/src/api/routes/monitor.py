"""
监控任务 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.core.database import get_db
from src.services.monitor_service import MonitorService
from src.api.routes.auth import get_current_user
from src.models.auth import User

router = APIRouter()


class CreateMonitorTaskRequest(BaseModel):
    """创建监控任务请求"""
    train_no: str
    from_station: str
    to_station: str
    travel_date: str  # YYYY-MM-DD
    seat_types: List[str]
    min_tickets: int = 1


class MonitorTaskResponse(BaseModel):
    """监控任务响应"""
    task_id: int
    train_no: str
    from_station: str
    to_station: str
    travel_date: str
    seat_types: List[str]
    min_tickets: int
    is_active: bool
    last_check_time: Optional[str]
    last_ticket_status: str
    created_at: str


@router.post("/tasks", response_model=MonitorTaskResponse)
async def create_monitor_task(
    request: CreateMonitorTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建监控任务"""
    try:
        monitor_service = MonitorService(db)
        
        # 解析日期
        travel_date = datetime.strptime(request.travel_date, "%Y-%m-%d")
        
        # 创建任务
        task = await monitor_service.create_monitor_task(
            user_id=current_user.id,
            train_no=request.train_no,
            from_station=request.from_station,
            to_station=request.to_station,
            travel_date=travel_date,
            seat_types=request.seat_types,
            min_tickets=request.min_tickets,
        )
        
        return MonitorTaskResponse(
            task_id=task.id,
            train_no=task.train_no,
            from_station=task.from_station,
            to_station=task.to_station,
            travel_date=task.travel_date.strftime("%Y-%m-%d"),
            seat_types=task.seat_types,
            min_tickets=task.min_tickets,
            is_active=task.is_active,
            last_check_time=task.last_check_time.isoformat() if task.last_check_time else None,
            last_ticket_status=task.last_ticket_status,
            created_at=task.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建监控任务失败：{str(e)}",
        )


@router.get("/tasks", response_model=List[MonitorTaskResponse])
async def get_monitor_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的监控任务列表"""
    monitor_service = MonitorService(db)
    tasks = await monitor_service.get_user_tasks(current_user.id)
    
    return [
        MonitorTaskResponse(
            task_id=task.id,
            train_no=task.train_no,
            from_station=task.from_station,
            to_station=task.to_station,
            travel_date=task.travel_date.strftime("%Y-%m-%d"),
            seat_types=task.seat_types,
            min_tickets=task.min_tickets,
            is_active=task.is_active,
            last_check_time=task.last_check_time.isoformat() if task.last_check_time else None,
            last_ticket_status=task.last_ticket_status,
            created_at=task.created_at.isoformat(),
        )
        for task in tasks
    ]


@router.post("/tasks/{task_id}/stop")
async def stop_monitor_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """停止监控任务"""
    monitor_service = MonitorService(db)
    task = await monitor_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    await monitor_service.stop_monitoring(task_id)
    
    return {"message": "监控任务已停止"}


@router.delete("/tasks/{task_id}")
async def delete_monitor_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除监控任务"""
    monitor_service = MonitorService(db)
    task = await monitor_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    await monitor_service.delete_task(task_id)
    
    return {"message": "监控任务已删除"}


@router.get("/tasks/{task_id}/logs")
async def get_monitor_task_logs(
    task_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取监控任务日志"""
    monitor_service = MonitorService(db)
    task = await monitor_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此任务")
    
    logs = await monitor_service.get_task_logs(task_id, limit)
    
    return [
        {
            "log_id": log.id,
            "check_time": log.check_time.isoformat(),
            "ticket_status": log.ticket_status,
            "ticket_count": log.ticket_count,
            "action_taken": log.action_taken,
            "message": log.message,
        }
        for log in logs
    ]
