"""
速率限制器 - 防封号策略
"""
import asyncio
import time
from typing import Optional
from loguru import logger
import random


class RateLimiter:
    """
    速率限制器
    用于控制请求频率，避免被封号
    """

    def __init__(
        self,
        min_interval: float = 3.0,
        max_interval: float = 5.0,
        max_requests_per_minute: int = 20,
    ):
        """
        初始化速率限制器
        参数:
            min_interval: 最小请求间隔（秒）
            max_interval: 最大请求间隔（秒，添加随机性）
            max_requests_per_minute: 每分钟最大请求数
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.max_requests_per_minute = max_requests_per_minute
        
        self.last_request_time: Optional[float] = None
        self.request_times = []
        self._lock = asyncio.Lock()

    async def wait_if_needed(self):
        """如果需要，等待以满足速率限制"""
        async with self._lock:
            current_time = time.time()
            
            # 清理 1 分钟前的请求记录
            self.request_times = [
                t for t in self.request_times 
                if current_time - t < 60
            ]

            # 检查每分钟请求数限制
            if len(self.request_times) >= self.max_requests_per_minute:
                oldest_request = min(self.request_times)
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    logger.debug(f"达到每分钟请求上限，等待 {wait_time:.2f} 秒")
                    await asyncio.sleep(wait_time)
                    self.request_times = []

            # 检查请求间隔
            if self.last_request_time:
                elapsed = current_time - self.last_request_time
                if elapsed < self.min_interval:
                    # 添加随机延迟模拟人类行为
                    random_delay = random.uniform(0, self.max_interval - self.min_interval)
                    wait_time = (self.min_interval - elapsed) + random_delay
                    logger.debug(f"请求间隔过短，等待 {wait_time:.2f} 秒")
                    await asyncio.sleep(wait_time)

            # 更新请求时间
            self.last_request_time = time.time()
            self.request_times.append(self.last_request_time)

    def reset(self):
        """重置限制器"""
        self.last_request_time = None
        self.request_times = []


class BehavioralSimulator:
    """
    行为模拟器
    模拟人类操作行为，增加随机性
    """

    @staticmethod
    async def human_like_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
        """模拟人类操作的随机延迟"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    @staticmethod
    def random_user_agent() -> str:
        """随机选择 User-Agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]
        return random.choice(user_agents)

    @staticmethod
    def random_headers() -> dict:
        """生成随机请求头"""
        return {
            "User-Agent": BehavioralSimulator.random_user_agent(),
            "Accept-Language": random.choice(["zh-CN,zh;q=0.9", "zh-CN,zh;q=0.9,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate, br",
        }
