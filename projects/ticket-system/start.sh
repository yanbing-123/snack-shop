#!/bin/bash

# 火车票抢票系统 - 快速启动脚本

set -e

echo "🚄 火车票抢票系统 - 启动脚本"
echo "=============================="

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✓ Python 版本：$python_version"

# 检查配置文件
if [ ! -f "config/.env" ]; then
    echo "⚠️  配置文件不存在，从模板复制..."
    cp config/.env.example config/.env
    echo "⚠️  请编辑 config/.env 填入实际配置值"
    exit 1
fi

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install -r requirements.txt

# 检查数据库连接
echo ""
echo "🔍 检查数据库连接..."
python -c "
import asyncio
from src.config.settings import settings

async def check_db():
    try:
        from src.core.database import database
        await database.connect()
        await database.disconnect()
        print('✓ 数据库连接成功')
        return True
    except Exception as e:
        print(f'✗ 数据库连接失败：{e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
" || {
    echo "⚠️  请先配置并启动数据库"
    exit 1
}

# 检查 Redis 连接
echo ""
echo "🔍 检查 Redis 连接..."
python -c "
import redis
from src.config.settings import settings

try:
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    print('✓ Redis 连接成功')
except Exception as e:
    print(f'✗ Redis 连接失败：{e}')
    exit(1)
" || {
    echo "⚠️  请先启动 Redis"
    exit 1
}

# 启动应用
echo ""
echo "🚀 启动应用..."
echo "访问 API 文档：http://localhost:8000/api/docs"
echo "按 Ctrl+C 停止服务"
echo ""

python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
