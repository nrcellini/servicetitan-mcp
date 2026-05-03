"""Documentation resources for MCP clients."""

from __future__ import annotations

from mcp.server.fastmcp.resources import HttpResource

# Canonical plain-text bundle of MCP docs for LLM context.
MCP_LLMS_FULL_URL = "https://modelcontextprotocol.io/llms-full.txt"


def mcp_llms_full_resource() -> HttpResource:
    """Full MCP documentation as published at modelcontextprotocol.io (llms-full.txt)."""
    return HttpResource(
        uri=MCP_LLMS_FULL_URL,
        url=MCP_LLMS_FULL_URL,
        name="mcp-llms-full",
        title="MCP LLM Full",
        description=(
            "Complete Model Context Protocol documentation as plain text (llms-full.txt). "
            "Reference for protocol concepts, tools, resources, prompts, and transports."
        ),
        mime_type="text/plain",
    )
