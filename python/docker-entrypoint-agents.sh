#!/bin/sh
# This script is the entrypoint for the Agents server Docker container.
# It handles environment variable setup and then executes the main application.

# Exit immediately if a command exits with a non-zero status.
set -e

# Use the value of $PORT if ARCHON_AGENTS_PORT is not set.
# This makes the container compatible with cloud environments like Render.
export ARCHON_AGENTS_PORT=${ARCHON_AGENTS_PORT:-$PORT}

# Check if the port is set
if [ -z "$ARCHON_AGENTS_PORT" ]; then
  echo "Error: ARCHON_AGENTS_PORT or PORT must be set." >&2
  exit 1
fi

echo "Starting Agents Server on port $ARCHON_AGENTS_PORT"

# Execute the main process, replacing the shell process.
exec python -m uvicorn src.agents.server:app --host 0.0.0.0 --port $ARCHON_AGENTS_PORT
