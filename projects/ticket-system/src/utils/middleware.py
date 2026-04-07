"""
中间件模块
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
from collections import defaultdict
from datetime import datetime, timedelta


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    防止 API 滥用
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # 清理 1 分钟前的请求记录
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip]
            if current_time - t < 60
        ]

        # 检查请求频率
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            logger.warning(f"速率限制：IP {client_ip} 超过请求限制")
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "data": None,
                },
            )

        # 记录请求
        self.request_history[client_ip].append(current_time)

        # 处理请求
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.request_history[client_ip])
        )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    日志中间件
    记录所有请求
    """

    async def dispatch(self, request: Request, call_next):
        # 记录请求
        logger.info(
            f"请求：{request.method} {request.url.path} - "
            f"IP: {request.client.host}"
        )

        # 处理请求
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 记录响应
        logger.info(
            f"响应：{request.method} {request.url.path} - "
            f"状态：{response.status_code} - "
            f"耗时：{process_time:.3f}s"
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全头中间件
    添加安全相关的 HTTP 头
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
