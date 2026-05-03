"""MCP entry point at src/server.py for Inspector and `mcp run`.

The MCP CLI adds this file's directory (`src/`) to sys.path before loading, so
`import servicetitan_mcp` resolves without extra configuration.
"""

from servicetitan_mcp.server import mcp

__all__ = ["mcp"]
