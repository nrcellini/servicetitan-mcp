#!/usr/bin/env bash
# MCP Inspector: absolute paths + mcp[cli] for the Inspector-spawned uv environment.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_FILE="$(cd "$REPO_ROOT" && pwd)/src/server.py"
cd "$REPO_ROOT"
exec npx -y @modelcontextprotocol/inspector \
  uv run --with "mcp[cli]" --with-editable "$REPO_ROOT" \
  mcp run "$SERVER_FILE"
