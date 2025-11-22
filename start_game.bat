@echo off
title Texas Hold'em Server

echo ===================================================
echo        Starting Texas Hold'em AI Battle...
echo ===================================================

:: 1. 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run "python -m venv venv" and "pip install -r requirements.txt" first.
    pause
    exit /b
)

:: 2. 启动浏览器打开前端页面 (使用默认浏览器)
echo [INFO] Opening Game Client...
start "" "frontend\index.html"

:: 3. 激活虚拟环境并启动后端服务器
echo [INFO] Starting Backend Server...
call venv\Scripts\activate.bat
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

pause