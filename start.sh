#!/bin/bash

# 启动智能旅行助手服务
echo "🚀 启动智能旅行助手服务..."

# 启动后端
echo "
🔧 启动后端服务..."
cd "$(dirname "$0")/backend"
python3 -m uvicorn app.main:app --reload --port 8000
