#!/bin/bash

# 1. 解決 Port 衝突：MCP 與 Agents 必須使用各自獨立的內部連接埠
# 透過覆寫 PORT 變數，防止它們去搶 Render 配發給主伺服器的外部 PORT
export ARCHON_MCP_PORT=${ARCHON_MCP_PORT:-8051}
export ARCHON_AGENTS_PORT=${ARCHON_AGENTS_PORT:-8052}
export ARCHON_SERVER_PORT=${PORT:-8181}
export ARCHON_SERVER_HOST=${ARCHON_SERVER_HOST:-127.0.0.1}

# 2. 記憶體優化 (Render 512MB 免費額度防禦)：
# 預設不自動啟動背景的 MCP 與 Agents 服務，以節省記憶體。
# 如果需要啟動，請在 Render 後台設定環境變數 `START_MCP=true` 或 `START_AGENTS=true`。

if [ "$START_MCP" = "true" ]; then
    echo "Starting MCP Server (Internal Port: $ARCHON_MCP_PORT)..."
    PORT=$ARCHON_MCP_PORT sh /app/docker-entrypoint-mcp.sh &
else
    echo "MCP Server is disabled. (Set START_MCP=true to enable)"
fi

if [ "$START_AGENTS" = "true" ]; then
    echo "Starting Agents Service (Internal Port: $ARCHON_AGENTS_PORT)..."
    PORT=$ARCHON_AGENTS_PORT sh /app/docker-entrypoint-agents.sh &
else
    echo "Agents Service is disabled. (Set START_AGENTS=true to enable)"
fi

# 3. 啟動主 FastAPI 服務 (在前景運行，接管對外 PORT)
echo "Starting Main FastAPI Server on port ${PORT:-8181}..."
python -m uvicorn src.server.main:app --host 0.0.0.0 --port ${PORT:-8181} --workers 1
