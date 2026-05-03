#!/usr/bin/env bash
# Same as scripts/mcp-dev.ps1: mcp dev with repo paths + auto free Inspector ports.
set -euo pipefail

_find_free_port() {
  local start="$1"
  python3 -c "
import socket
start = int('${start}')
for i in range(64):
    p = start + i
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('0.0.0.0', p))
        print(p)
        break
    except OSError:
        continue
    finally:
        s.close()
else:
    raise SystemExit('no free port from %s' % start)
"
}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER_FILE="$(cd "$REPO_ROOT" && pwd)/src/server.py"
cd "$REPO_ROOT"

if [ "${MCP_INSPECTOR_AUTO_PORT:-1}" = "1" ]; then
  export CLIENT_PORT="${CLIENT_PORT:-$(_find_free_port 6274)}"
  export SERVER_PORT="${SERVER_PORT:-$(_find_free_port 6277)}"
  if [ "$SERVER_PORT" = "$CLIENT_PORT" ]; then
    export SERVER_PORT="$(_find_free_port "$((CLIENT_PORT + 1))")"
  fi
  echo "MCP Inspector: CLIENT_PORT=${CLIENT_PORT} SERVER_PORT=${SERVER_PORT}" >&2
else
  export CLIENT_PORT="${CLIENT_PORT:-6274}"
  export SERVER_PORT="${SERVER_PORT:-6277}"
fi

exec uv run --extra dev mcp dev --with-editable "$REPO_ROOT" "$SERVER_FILE"
