"""
12306 API 服务 - 车次查询、余票监控、自动抢票
"""
import httpx
import asyncio
from typing import Optional, List, Dict
from datetime import datetime, date
from loguru import logger
from src.config.settings import settings
from src.utils.rate_limiter import RateLimiter
import random
import time


class RailwayService:
    """12306 服务类"""

    # 12306 API 端点
    BASE_URL = "https://kyfw.12306.cn"
    LEFT_TICKET_URL = "https://kyfw.12306.cn/otn/leftTicket/query"
    SUBMIT_ORDER_URL = "https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest"
    CONFIRM_ORDER_URL = "https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue"

    # 座位类型映射
    SEAT_TYPE_MAP = {
        "商务座": "32",
        "一等座": "31",
        "二等座": "30",
        "特等座": "25",
        "动卧": "33",
        "硬卧": "23",
        "软卧": "24",
        "硬座": "26",
        "软座": "25",
        "无座": "26",
    }

    def __init__(self):
        self.session = None
        self.rate_limiter = RateLimiter(
            min_interval=settings.QUERY_INTERVAL_SECONDS,
            max_requests_per_minute=20
        )
        self.cookies = {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    async def init_session(self):
        """初始化 HTTP 会话"""
        if not self.session:
            self.session = httpx.AsyncClient(
                cookies=self.cookies,
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True,
            )

    async def close(self):
        """关闭会话"""
        if self.session:
            await self.session.aclose()
            self.session = None

    async def login(self, username: str, password: str) -> bool:
        """
        登录 12306
        注意：实际实现需要处理验证码，这里提供框架
        """
        await self.init_session()

        try:
            # 1. 获取登录页面（获取 cookies）
            await self.session.get(f"{self.BASE_URL}/otn/login/loginAuth")
            await asyncio.sleep(random.uniform(1, 2))  # 模拟人类行为

            # 2. 登录请求（实际需要处理验证码）
            login_data = {
                "username": username,
                "password": password,
                # 需要添加验证码相关参数
            }

            # 注意：完整实现需要集成打码平台或手动验证码
            logger.warning("12306 登录需要验证码处理，请使用 playwright 实现浏览器自动化")
            
            return True
        except Exception as e:
            logger.error(f"登录失败：{e}")
            return False

    async def query_tickets(
        self,
        from_station: str,
        to_station: str,
        travel_date: str,
    ) -> List[Dict]:
        """
        查询余票
        参数:
            from_station: 始发站（中文）
            to_station: 终点站（中文）
            travel_date: 出行日期（YYYY-MM-DD）
        返回:
            车次和余票信息列表
        """
        await self.init_session()
        
        # 频率限制
        await self.rate_limiter.wait_if_needed()

        try:
            # 获取车站代码
            from_code = await self._get_station_code(from_station)
            to_code = await self._get_station_code(to_station)

            if not from_code or not to_code:
                logger.error(f"车站代码查询失败：{from_station} -> {to_station}")
                return []

            # 构建查询 URL
            params = {
                "leftTicketDTO.train_date": travel_date,
                "leftTicketDTO.from_station": from_code,
                "leftTicketDTO.to_station": to_code,
                "purpose_codes": "ADULT",
            }

            # 添加随机延迟模拟人类行为
            await asyncio.sleep(random.uniform(0.5, 1.5))

            response = await self.session.get(
                self.LEFT_TICKET_URL,
                params=params,
            )

            if response.status_code != 200:
                logger.error(f"查询失败：HTTP {response.status_code}")
                return []

            data = response.json()
            if data.get("status") and "data" in data:
                return self._parse_ticket_data(data["data"])
            
            return []
        except Exception as e:
            logger.error(f"查询余票异常：{e}")
            return []

    def _parse_ticket_data(self, data: Dict) -> List[Dict]:
        """解析余票数据"""
        results = []
        
        result_list = data.get("result", [])
        for item in result_list:
            if not isinstance(item, str):
                continue
                
            fields = item.split("|")
            if len(fields) < 40:
                continue

            # 字段索引参考 12306 API 文档
            train_info = {
                "train_no": fields[3],  # 车次编号
                "from_station": fields[6],  # 始发站
                "to_station": fields[7],  # 终点站
                "from_time": fields[8],  # 发车时间
                "to_time": fields[9],  # 到达时间
                "duration": fields[10],  # 历时
                "ticket_status": fields[11],  # 余票状态
                "seat_types": {
                    "商务座": fields[32] if len(fields) > 32 else "",
                    "一等座": fields[31] if len(fields) > 31 else "",
                    "二等座": fields[30] if len(fields) > 30 else "",
                    "硬卧": fields[28] if len(fields) > 28 else "",
                    "软卧": fields[23] if len(fields) > 23 else "",
                    "硬座": fields[29] if len(fields) > 29 else "",
                },
                "raw_data": fields,
            }
            results.append(train_info)

        return results

    async def _get_station_code(self, station_name: str) -> Optional[str]:
        """
        获取车站代码
        实际实现需要查询车站代码映射表
        """
        # 简化实现：这里应该查询车站代码数据库
        # 示例：北京 -> BJP, 上海 -> SHH
        station_codes = {
            "北京": "BJP",
            "上海": "SHH",
            "广州": "GZQ",
            "深圳": "SZQ",
            # ... 更多车站
        }
        return station_codes.get(station_name)

    async def submit_order(
        self,
        ticket_info: Dict,
        passenger_ids: List[str],
        seat_type: str,
    ) -> Optional[Dict]:
        """
        提交订单
        返回订单信息或 None
        """
        await self.init_session()
        await self.rate_limiter.wait_if_needed()

        try:
            # 构建订单数据
            order_data = {
                "secretStr": ticket_info.get("secretStr"),
                "train_date": ticket_info.get("train_date"),
                "train_no": ticket_info.get("train_no"),
                "stationTrainCode": ticket_info.get("stationTrainCode"),
                "seatType": self.SEAT_TYPE_MAP.get(seat_type, "30"),
                "fromStationTelecode": ticket_info.get("fromStationTelecode"),
                "toStationTelecode": ticket_info.get("toStationTelecode"),
                "leftTicket": ticket_info.get("leftTicket"),
                "purpose_codes": "ADULT",
                "passengerTicketStr": self._build_passenger_string(passenger_ids, seat_type),
                "oldPassengerStr": self._build_old_passenger_string(passenger_ids),
            }

            response = await self.session.post(
                self.SUBMIT_ORDER_URL,
                data=order_data,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status"):
                    logger.info(f"订单提交成功：{result.get('data', {})}")
                    return result.get("data")
            
            logger.error(f"订单提交失败：{response.text}")
            return None
        except Exception as e:
            logger.error(f"提交订单异常：{e}")
            return None

    def _build_passenger_string(self, passenger_ids: List[str], seat_type: str) -> str:
        """构建乘车人字符串"""
        # 格式：1,0,1,张三，1，身份证号，手机号，N
        passengers = []
        for i, pid in enumerate(passenger_ids, 1):
            passengers.append(f"1,0,1,{pid},1，身份证号，手机号，N")
        return "_".join(passengers)

    def _build_old_passenger_string(self, passenger_ids: List[str]) -> str:
        """构建旧乘车人字符串"""
        passengers = []
        for pid in passenger_ids:
            passengers.append(f"1,姓名，1，身份证号，N")
        return "_".join(passengers)

    async def confirm_order(self, order_info: Dict) -> bool:
        """确认订单并支付"""
        await self.init_session()
        
        try:
            confirm_data = {
                "passengerTicketStr": order_info.get("passengerTicketStr"),
                "oldPassengerStr": order_info.get("oldPassengerStr"),
                "purpose_codes": "ADULT",
                "key_check_isChange": order_info.get("key_check_isChange"),
                "leftTicketStr": order_info.get("leftTicketStr"),
                "train_location": order_info.get("train_location"),
                "seatDetailType": "0",
                "roomType": "00",
                "dwAll": "N",
            }

            response = await self.session.post(
                self.CONFIRM_ORDER_URL,
                data=confirm_data,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("status", False)
            
            return False
        except Exception as e:
            logger.error(f"确认订单异常：{e}")
            return False


# 全局服务实例
railway_service = RailwayService()
