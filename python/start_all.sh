#!/bin/bash
# 啟動 MCP 服務 (在背景執行)
echo "Starting MCP Server..."
sh /app/docker-entrypoint-mcp.sh &

# 啟動 Agents 服務 (在背景執行)
echo "Starting Agents Service..."
sh /app/docker-entrypoint-agents.sh &

# 啟動主 FastAPI 服務 (在前景執行，負責監聽 Render 給的 PORT)
echo "Starting Main FastAPI Server..."
# 注意：這裡修正了原本的 socket_app 錯誤，改為正確的 main:app
python -m uvicorn src.server.main:app --host 0.0.0.0 --port ${PORT:-8181} --workers 1
