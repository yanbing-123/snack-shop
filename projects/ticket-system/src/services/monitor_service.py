"""
余票监控服务
"""
import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger
from src.models.ticket import MonitorTask, MonitorTaskLog, Ticket
from src.services.railway_service import railway_service
from src.services.notification_service import NotificationService
from src.config.settings import settings


class MonitorService:
    """余票监控服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService()
        self.running_tasks = {}  # 存储运行中的监控任务
        self.is_running = False

    async def create_monitor_task(
        self,
        user_id: int,
        train_no: str,
        from_station: str,
        to_station: str,
        travel_date: datetime,
        seat_types: List[str],
        min_tickets: int = 1,
    ) -> MonitorTask:
        """创建监控任务"""
        task = MonitorTask(
            user_id=user_id,
            train_no=train_no,
            from_station=from_station,
            to_station=to_station,
            travel_date=travel_date,
            seat_types=seat_types,
            min_tickets=min_tickets,
            is_active=True,
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        logger.info(f"创建监控任务：{task.id} - {train_no} {from_station}->{to_station}")
        
        # 启动监控
        await self.start_monitoring(task.id)

        return task

    async def start_monitoring(self, task_id: int):
        """启动监控任务"""
        if task_id in self.running_tasks:
            logger.warning(f"监控任务已在运行：{task_id}")
            return

        task = await self.get_task(task_id)
        if not task or not task.is_active:
            logger.error(f"监控任务不存在或已禁用：{task_id}")
            return

        # 创建异步任务
        asyncio_task = asyncio.create_task(self._monitor_loop(task))
        self.running_tasks[task_id] = asyncio_task
        logger.info(f"监控任务已启动：{task_id}")

    async def stop_monitoring(self, task_id: int):
        """停止监控任务"""
        if task_id not in self.running_tasks:
            return

        # 更新任务状态
        await self.db.execute(
            update(MonitorTask)
            .where(MonitorTask.id == task_id)
            .values(is_active=False)
        )
        await self.db.commit()

        # 取消异步任务
        task = self.running_tasks[task_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        del self.running_tasks[task_id]
        logger.info(f"监控任务已停止：{task_id}")

    async def _monitor_loop(self, task: MonitorTask):
        """监控循环"""
        try:
            while task.is_active:
                # 查询余票
                ticket_info = await railway_service.query_tickets(
                    from_station=task.from_station,
                    to_station=task.to_station,
                    travel_date=task.travel_date.strftime("%Y-%m-%d"),
                )

                # 检查目标车次
                target_train = None
                for train in ticket_info:
                    if train.get("train_no") == task.train_no:
                        target_train = train
                        break

                # 记录日志
                if target_train:
                    await self._log_check(task.id, "CHECKED", len(target_train.get("seat_types", {})))
                    
                    # 检查余票
                    has_tickets = False
                    for seat_type in task.seat_types:
                        ticket_count = target_train.get("seat_types", {}).get(seat_type, "")
                        if ticket_count and ticket_count != "无" and ticket_count != "":
                            has_tickets = True
                            logger.info(f"监控到余票：{task.train_no} {seat_type} {ticket_count}")
                            
                            # 发送通知
                            await self.notification_service.send_notification(
                                user_id=task.user_id,
                                title="余票提醒",
                                message=f"{task.train_no} 次列车 {seat_type} 有余票：{ticket_count}",
                            )
                            break

                    if has_tickets:
                        # 可选：自动抢票
                        # await self._auto_book(task, target_train)
                        pass
                else:
                    await self._log_check(task.id, "NOT_FOUND", 0)

                # 等待下次检查
                await asyncio.sleep(settings.MONITOR_MIN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            logger.info(f"监控任务被取消：{task.id}")
        except Exception as e:
            logger.error(f"监控任务异常：{task.id}, 错误：{e}")

    async def _log_check(self, task_id: int, status: str, ticket_count: int):
        """记录检查日志"""
        log = MonitorTaskLog(
            task_id=task_id,
            ticket_status=status,
            ticket_count=ticket_count,
            action_taken="NONE",
        )
        self.db.add(log)

        # 更新任务最后检查时间
        await self.db.execute(
            update(MonitorTask)
            .where(MonitorTask.id == task_id)
            .values(
                last_check_time=datetime.utcnow(),
                last_ticket_status=status,
            )
        )

        await self.db.commit()

    async def get_task(self, task_id: int) -> Optional[MonitorTask]:
        """获取监控任务"""
        result = await self.db.execute(
            select(MonitorTask).where(MonitorTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_user_tasks(self, user_id: int) -> List[MonitorTask]:
        """获取用户的监控任务列表"""
        result = await self.db.execute(
            select(MonitorTask)
            .where(MonitorTask.user_id == user_id)
            .order_by(MonitorTask.created_at.desc())
        )
        return result.scalars().all()

    async def update_task(self, task_id: int, **kwargs):
        """更新监控任务"""
        await self.db.execute(
            update(MonitorTask)
            .where(MonitorTask.id == task_id)
            .values(**kwargs)
        )
        await self.db.commit()

    async def delete_task(self, task_id: int):
        """删除监控任务"""
        # 先停止监控
        await self.stop_monitoring(task_id)

        # 删除任务
        task = await self.get_task(task_id)
        if task:
            await self.db.delete(task)
            await self.db.commit()
            logger.info(f"监控任务已删除：{task_id}")

    async def get_task_logs(self, task_id: int, limit: int = 50) -> List[MonitorTaskLog]:
        """获取监控任务日志"""
        result = await self.db.execute(
            select(MonitorTaskLog)
            .where(MonitorTaskLog.task_id == task_id)
            .order_by(MonitorTaskLog.check_time.desc())
            .limit(limit)
        )
        return result.scalars().all()
