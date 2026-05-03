#!/usr/bin/env bash
# MCP Inspector: absolute paths + mcp[cli] for the Inspector-spawned uv environment.
# Override ports if 6274/6277 are busy: CLIENT_PORT=6284 SERVER_PORT=6287 ./scripts/mcp-inspector.sh
set -euo pipefail
export CLIENT_PORT="${CLIENT_PORT:-6274}"
export SERVER_PORT="${SERVER_PORT:-6277}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_FILE="$(cd "$REPO_ROOT" && pwd)/src/server.py"
cd "$REPO_ROOT"
exec npx -y @modelcontextprotocol/inspector \
  uv run --with "mcp[cli]" --with-editable "$REPO_ROOT" \
  mcp run "$SERVER_FILE"
