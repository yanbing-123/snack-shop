# 火车票抢票系统

实时余票监控与自动抢票系统，基于 FastAPI + PostgreSQL + Redis 构建。

## ⚠️ 重要声明

本系统仅供学习研究使用，请勿用于商业目的或大规模抢票。使用本系统可能违反 12306 相关规定，请谨慎使用。

## 功能特性

- ✅ 用户注册/登录与 Token 管理
- ✅ 12306 账号管理（加密存储）
- ✅ 车次查询与余票监控
- ✅ 自动抢票与订单管理
- ✅ 乘车人管理
- ✅ 多渠道通知（邮件/短信/推送）
- ✅ 防封号策略（请求频率控制、行为模拟）
- ✅ RESTful API 接口

## 技术栈

- **后端框架**: FastAPI 0.109.0
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **ORM**: SQLAlchemy 2.0 (Async)
- **HTTP 客户端**: Httpx + Playwright
- **认证**: JWT (PyJWT)
- **加密**: Cryptography + Bcrypt
- **任务队列**: Celery 5.3.6

## 项目结构

```
ticket-system/
├── src/                          # 源代码
│   ├── api/                      # API 路由
│   │   └── routes/               # 路由模块
│   │       ├── auth.py           # 认证路由
│   │       ├── tickets.py        # 车次查询路由
│   │       ├── monitor.py        # 监控任务路由
│   │       ├── orders.py         # 订单管理路由
│   │       └── passengers.py     # 乘车人管理路由
│   ├── config/                   # 配置文件
│   │   ├── settings.py           # 应用配置
│   │   └── .env.example          # 环境变量示例
│   ├── core/                     # 核心模块
│   │   └── database.py           # 数据库连接
│   ├── models/                   # 数据模型
│   │   ├── auth.py               # 用户认证模型
│   │   └── ticket.py             # 车次订单模型
│   ├── services/                 # 业务服务
│   │   ├── auth_service.py       # 认证服务
│   │   ├── railway_service.py    # 12306 服务
│   │   ├── monitor_service.py    # 监控服务
│   │   └── notification_service.py # 通知服务
│   ├── utils/                    # 工具函数
│   │   ├── encryption.py         # 加密工具
│   │   ├── rate_limiter.py       # 速率限制
│   │   └── middleware.py         # 中间件
│   └── main.py                   # 应用入口
├── database/                     # 数据库脚本
│   ├── create_tables.sql         # 建表脚本
│   └── alembic.ini               # Alembic 配置
├── config/                       # 运行配置
│   └── .env.example              # 环境变量模板
├── tests/                        # 测试文件
├── requirements.txt              # Python 依赖
└── README.md                     # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- PostgreSQL 15+
- Redis 7+

### 2. 安装依赖

```bash
cd ticket-system
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp config/.env.example config/.env

# 编辑配置文件，填入实际值
# 必填项：
# - DATABASE_URL
# - DATABASE_ASYNC_URL
# - JWT_SECRET_KEY
# - ENCRYPTION_KEY
```

### 4. 初始化数据库

```bash
# 方式 1：使用 SQL 脚本
psql -U postgres -f database/create_tables.sql

# 方式 2：使用 Alembic 迁移
cd database
alembic upgrade head
```

### 5. 启动 Redis

```bash
# macOS
brew install redis
redis-server

# Windows
# 下载 Redis for Windows 或使用 WSL
redis-server
```

### 6. 启动应用

```bash
# 开发模式（自动重载）
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 访问 API 文档

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- 健康检查：http://localhost:8000/health

## API 使用示例

### 用户注册

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

### 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123"
  }'
```

### 查询余票

```bash
curl -X GET "http://localhost:8000/api/v1/tickets/query?from_station=北京&to_station=上海&travel_date=2024-02-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 创建监控任务

```bash
curl -X POST http://localhost:8000/api/v1/monitor/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "train_no": "G123",
    "from_station": "北京",
    "to_station": "上海",
    "travel_date": "2024-02-01",
    "seat_types": ["二等座", "一等座"],
    "min_tickets": 1
  }'
```

## 核心功能说明

### 1. 用户认证

- JWT Token 认证（Access Token + Refresh Token）
- 密码 bcrypt 加密存储
- Token 自动刷新机制

### 2. 12306 账号管理

- 12306 账号密码加密存储（Fernet 对称加密）
- 支持多账号管理
- 自动登录与 Cookie 维护

### 3. 余票监控

- 定时查询余票（可配置间隔）
- 多车次、多座位类型监控
- 余票变化实时通知

### 4. 自动抢票

- 监控到余票自动下单
- 支持多个乘车人
- 订单状态跟踪

### 5. 通知服务

- 邮件通知（SMTP）
- 短信通知（阿里云）
- 推送通知（可扩展）

### 6. 防封号策略

- 请求频率限制（可配置）
- 随机延迟模拟人类行为
- User-Agent 轮换
- IP 代理支持（需自行配置）

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | PostgreSQL 连接 URL | 必填 |
| REDIS_URL | Redis 连接 URL | redis://localhost:6379/0 |
| JWT_SECRET_KEY | JWT 密钥 | 必填 |
| ENCRYPTION_KEY | 加密密钥 | 必填 |
| SMTP_SERVER | SMTP 服务器 | smtp.qq.com |
| SMTP_PORT | SMTP 端口 | 587 |
| QUERY_INTERVAL_SECONDS | 查询间隔（秒） | 3 |
| MONITOR_MIN_INTERVAL_SECONDS | 监控最小间隔（秒） | 30 |

### 频率限制配置

```python
# 防封号推荐配置
QUERY_INTERVAL_SECONDS = 3        # 查询间隔 >= 3 秒
MONITOR_MIN_INTERVAL_SECONDS = 30  # 监控间隔 >= 30 秒
MAX_RETRY_ATTEMPTS = 3            # 最大重试次数
```

## 测试

```bash
# 运行测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_auth.py -v

# 生成覆盖率报告
pytest --cov=src tests/
```

## 部署

### Docker 部署（推荐）

```bash
# 构建镜像
docker build -t ticket-system .

# 运行容器
docker run -d \
  --name ticket-system \
  -p 8000:8000 \
  --env-file config/.env \
  ticket-system
```

### 生产环境建议

1. 使用 Gunicorn + Uvicorn Workers
2. 配置 Nginx 反向代理
3. 启用 HTTPS
4. 配置日志轮转
5. 监控与告警（Prometheus + Grafana）
6. 数据库备份策略

## 常见问题

### Q: 12306 登录需要验证码怎么办？

A: 当前版本使用 Playwright 实现浏览器自动化处理验证码。生产环境建议集成打码平台。

### Q: 如何配置代理 IP？

A: 在 `railway_service.py` 中配置代理：

```python
self.session = httpx.AsyncClient(
    proxy="http://proxy-host:proxy-port",
    # ...
)
```

### Q: 监控任务不生效？

A: 检查：
1. Redis 是否正常运行
2. 监控任务 `is_active` 状态
3. 日志文件 `logs/app_*.log`

## 开发计划

- [ ] 支持候补购票
- [ ] 智能推荐车次
- [ ] 多账号协同抢票
- [ ] 图形化管理界面
- [ ] 移动端 APP

## 许可证

MIT License

## 免责声明

本系统仅供学习研究使用。使用本系统可能违反 12306 官方网站的使用条款，请用户自行承担风险。作者不对使用本系统造成的任何损失负责。

---

**作者**: 小开  
**版本**: 1.0.0  
**更新时间**: 2024-01-20
