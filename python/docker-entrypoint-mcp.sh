#!/bin/sh
# This script is the entrypoint for the MCP server Docker container.
# It handles environment variable setup and then executes the main application.

# Exit immediately if a command exits with a non-zero status.
set -e

# Use the value of $PORT if ARCHON_MCP_PORT is not set.
# This makes the container compatible with cloud environments like Render.
export ARCHON_MCP_PORT=${ARCHON_MCP_PORT:-$PORT}

# Check if the port is set
if [ -z "$ARCHON_MCP_PORT" ]; then
  echo "Error: ARCHON_MCP_PORT or PORT must be set." >&2
  exit 1
fi

echo "Starting MCP Server on port $ARCHON_MCP_PORT"

# Execute the main process, replacing the shell process.
exec python -m src.mcp_server.mcp_server
