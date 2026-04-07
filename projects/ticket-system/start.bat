@echo off
chcp 65001 >nul
echo 🚄 火车票抢票系统 - 启动脚本
echo ==============================

REM 检查 Python 版本
python --version
echo ✓ Python 已安装

REM 检查配置文件
if not exist "config\.env" (
    echo ⚠️  配置文件不存在，从模板复制...
    copy config\.env.example config\.env
    echo ⚠️  请编辑 config\.env 填入实际配置值
    pause
    exit /b 1
)

REM 安装依赖
echo.
echo 📦 安装依赖...
pip install -r requirements.txt

REM 启动应用
echo.
echo 🚀 启动应用...
echo 访问 API 文档：http://localhost:8000/api/docs
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
