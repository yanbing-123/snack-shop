"""
通知服务 - 邮件、短信、推送
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from loguru import logger
from src.config.settings import settings
import requests
import asyncio


class NotificationService:
    """通知服务"""

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.notification_email = settings.NOTIFICATION_EMAIL

    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "email",
    ):
        """
        发送通知
        参数:
            user_id: 用户 ID
            title: 通知标题
            message: 通知内容
            notification_type: 通知类型 (email, sms, push)
        """
        try:
            if notification_type == "email":
                await self.send_email(title, message)
            elif notification_type == "sms":
                await self.send_sms(message)
            elif notification_type == "push":
                await self.send_push_notification(user_id, title, message)
            
            logger.info(f"通知发送成功：{title}")
        except Exception as e:
            logger.error(f"通知发送失败：{e}")

    async def send_email(self, subject: str, content: str, to_email: Optional[str] = None):
        """
        发送邮件
        """
        if not to_email:
            to_email = self.notification_email

        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))

            # 发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件发送成功：{subject}")
        except Exception as e:
            logger.error(f"邮件发送失败：{e}")
            raise

    async def send_sms(self, message: str, phone_number: Optional[str] = None):
        """
        发送短信（阿里云）
        """
        if not settings.ALIYUN_ACCESS_KEY_ID or not settings.ALIYUN_ACCESS_KEY_SECRET:
            logger.warning("未配置阿里云短信服务")
            return

        phone = phone_number or settings.ALIYUN_PHONE_NUMBER
        if not phone:
            logger.warning("未指定手机号")
            return

        try:
            # 阿里云短信 API 实现
            # 这里提供框架，实际使用需要集成阿里云 SDK
            logger.info(f"短信发送（模拟）：{phone} - {message}")
            
            # 示例代码（需要安装 aliyun-python-sdk-core）
            # from aliyunsdkcore.client import AcsClient
            # from aliyunsdkcore.request import CommonRequest
            # client = AcsClient(
            #     settings.ALIYUN_ACCESS_KEY_ID,
            #     settings.ALIYUN_ACCESS_KEY_SECRET,
            #     "cn-hangzhou"
            # )
            # request = CommonRequest()
            # request.set_method("POST")
            # request.set_domain("dysmsapi.aliyuncs.com")
            # request.set_version("2017-05-25")
            # request.set_action_name("SendSms")
            # request.add_query_param("PhoneNumbers", phone)
            # request.add_query_param("SignName", "你的签名")
            # request.add_query_param("TemplateCode", "你的模板代码")
            # request.add_query_param("TemplateParam", f'{{"message":"{message}"}}')
            # response = client.do_action_with_exception(request)

        except Exception as e:
            logger.error(f"短信发送失败：{e}")

    async def send_push_notification(
        self,
        user_id: int,
        title: str,
        message: str,
    ):
        """
        发送推送通知
        可以使用第三方推送服务（如极光推送、个推等）
        """
        try:
            # 这里提供框架，实际使用需要集成推送服务 SDK
            logger.info(f"推送通知（模拟）：用户 {user_id} - {title}: {message}")
            
            # 示例：WebSocket 推送
            # 或者集成第三方推送服务
            
        except Exception as e:
            logger.error(f"推送通知失败：{e}")

    async def send_ticket_alert(
        self,
        user_email: str,
        train_no: str,
        from_station: str,
        to_station: str,
        seat_type: str,
        ticket_count: str,
    ):
        """发送余票提醒邮件"""
        subject = f"🚄 余票提醒：{train_no} 次列车"
        content = f"""
余票提醒

车次：{train_no}
行程：{from_station} -> {to_station}
座位：{seat_type}
余票：{ticket_count}

请及时登录 12306 或抢票系统下单！

---
火车票抢票系统
"""
        await self.send_email(subject, content, user_email)

    async def send_order_success(
        self,
        user_email: str,
        order_no: str,
        train_no: str,
        from_station: str,
        to_station: str,
        travel_date: str,
        price: float,
    ):
        """发送订单成功通知"""
        subject = f"✅ 购票成功：{order_no}"
        content = f"""
购票成功通知

订单号：{order_no}
车次：{train_no}
行程：{from_station} -> {to_station}
日期：{travel_date}
金额：¥{price:.2f}

请及时登录 12306 查看订单详情！

---
火车票抢票系统
"""
        await self.send_email(subject, content, user_email)

    async def send_order_failure(
        self,
        user_email: str,
        train_no: str,
        from_station: str,
        to_station: str,
        reason: str,
    ):
        """发送抢票失败通知"""
        subject = f"❌ 抢票失败：{train_no} 次列车"
        content = f"""
抢票失败通知

车次：{train_no}
行程：{from_station} -> {to_station}
原因：{reason}

系统将继续为您监控余票，请保持关注。

---
火车票抢票系统
"""
        await self.send_email(subject, content, user_email)
