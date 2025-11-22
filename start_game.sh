#!/bin/bash

echo "==================================================="
echo "       Starting Texas Hold'em AI Battle..."
echo "==================================================="

# 1. 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run 'python3 -m venv venv' and install requirements first."
    exit 1
fi

# 2. 打开浏览器 (尝试不同的命令)
if which xdg-open > /dev/null; then
  xdg-open "frontend/index.html"
elif which open > /dev/null; then
  open "frontend/index.html"
else
  echo "[WARN] Could not open browser automatically. Please open frontend/index.html manually."
fi

# 3. 启动服务器
source venv/bin/activate
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000