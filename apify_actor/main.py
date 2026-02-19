"""Apify Actor entry point for ServiceTitan MCP Server.

This wraps the FastMCP server for deployment on the Apify platform.
Credentials are read from the Actor input configuration.

TODO (Day 3): Implement full Apify Actor lifecycle:
- Read input from Apify Actor input
- Set up pay-per-event billing hooks
- Handle Actor lifecycle events (init, run, cleanup)
- Implement SSE transport for MCP over HTTP
"""

from __future__ import annotations

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def main() -> None:
    """Actor main entry point."""
    # TODO (Day 3): Read from Apify Actor input
    # from apify import Actor
    # async with Actor:
    #     actor_input = await Actor.get_input() or {}
    #     os.environ["ST_CLIENT_ID"] = actor_input.get("ST_CLIENT_ID", "")
    #     os.environ["ST_CLIENT_SECRET"] = actor_input.get("ST_CLIENT_SECRET", "")
    #     os.environ["ST_APP_KEY"] = actor_input.get("ST_APP_KEY", "")
    #     os.environ["ST_TENANT_ID"] = actor_input.get("ST_TENANT_ID", "")
    #     os.environ["ST_ENVIRONMENT"] = actor_input.get("ST_ENVIRONMENT", "production")

    # For now, just start the MCP server
    from src.servicetitan_mcp.server import mcp
    mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
