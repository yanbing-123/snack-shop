"""
车次和订单相关模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from src.core.database import Base


class Train(Base):
    """车次信息模型"""
    __tablename__ = "trains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_no = Column(String(20), nullable=False, index=True)  # 车次编号，如 G123
    train_code = Column(String(20), nullable=False)  # 车次代码
    from_station = Column(String(50), nullable=False)  # 始发站
    to_station = Column(String(50), nullable=False)  # 终点站
    from_time = Column(String(10))  # 发车时间
    to_time = Column(String(10))  # 到达时间
    duration = Column(String(10))  # 历时
    distance = Column(Integer)  # 里程
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Ticket(Base):
    """余票信息模型"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    train_no = Column(String(20), nullable=False, index=True)
    from_station = Column(String(50), nullable=False)
    to_station = Column(String(50), nullable=False)
    travel_date = Column(DateTime, nullable=False, index=True)
    seat_type = Column(String(20), nullable=False)  # 座位类型
    price = Column(Float, nullable=False)  # 价格
    ticket_count = Column(Integer, default=0)  # 余票数量
    ticket_status = Column(String(20), default="AVAILABLE")  # AVAILABLE, INSUFFICIENT, SOLD_OUT
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MonitorTask(Base):
    """监控任务模型"""
    __tablename__ = "monitor_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    train_no = Column(String(20), nullable=False)
    from_station = Column(String(50), nullable=False)
    to_station = Column(String(50), nullable=False)
    travel_date = Column(DateTime, nullable=False)
    seat_types = Column(JSON)  # 监控的座位类型列表
    min_tickets = Column(Integer, default=1)  # 最小余票数量
    is_active = Column(Boolean, default=True)
    last_check_time = Column(DateTime, nullable=True)
    last_ticket_status = Column(String(20), default="UNKNOWN")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    user = relationship("User", back_populates="monitor_tasks")
    task_logs = relationship("MonitorTaskLog", back_populates="task", cascade="all, delete-orphan")


class MonitorTaskLog(Base):
    """监控任务日志模型"""
    __tablename__ = "monitor_task_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("monitor_tasks.id"), nullable=False, index=True)
    check_time = Column(DateTime, default=datetime.utcnow)
    ticket_status = Column(String(20))
    ticket_count = Column(Integer)
    action_taken = Column(String(50))  # 采取的动作：NOTIFY, BOOK, NONE
    message = Column(Text, nullable=True)

    # 关联
    task = relationship("MonitorTask", back_populates="task_logs")


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)  # 订单号
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    railway_account_id = Column(Integer, ForeignKey("railway_accounts.id"), nullable=False)
    train_no = Column(String(20), nullable=False)
    from_station = Column(String(50), nullable=False)
    to_station = Column(String(50), nullable=False)
    travel_date = Column(DateTime, nullable=False)
    seat_type = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    passengers = Column(JSON, nullable=False)  # 乘车人信息列表
    status = Column(String(20), default="PENDING")  # PENDING, SUCCESS, FAILED, CANCELLED, REFUNDED
    payment_status = Column(String(20), default="UNPAID")  # UNPAID, PAID, REFUNDED
    railway_order_no = Column(String(50), nullable=True)  # 12306 订单号
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # 关联
    user = relationship("User", back_populates="orders")
    railway_account = relationship("RailwayAccount")
