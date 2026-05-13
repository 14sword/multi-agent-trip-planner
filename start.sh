#!/bin/bash

# 启动智能旅行助手服务
echo "启动智能旅行助手服务..."

DIR="$(cd "$(dirname "$0")" && pwd)"

# 启动后端
echo "启动后端服务..."
cd "$DIR/backend"
python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "启动前端服务..."
cd "$DIR/frontend-redesigned"
npx vite --port 5173 &
FRONTEND_PID=$!

echo "服务已启动:"
echo "  后端: http://localhost:8000"
echo "  前端: http://localhost:5173"
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
