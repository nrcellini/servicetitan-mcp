"""ServiceTitan MCP Server — main entry point.

Exposes ServiceTitan tools via the Model Context Protocol (MCP)
using FastMCP. Supports job management, customer lookup,
scheduling, dispatching, and invoicing for home services contractors.
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

# `mcp dev path/to/server.py` loads this file via importlib as a top-level module, not as
# servicetitan_mcp.server — prepend the src root so absolute package imports resolve.
_src_root = Path(__file__).resolve().parent.parent
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from servicetitan_mcp.client import init_client, close_client
from servicetitan_mcp.models.types import ServiceTitanConfig
from servicetitan_mcp.tools.customers import search_customers, get_customer
from servicetitan_mcp.tools.jobs import list_jobs, get_job, create_job, list_jobs_with_details
from servicetitan_mcp.tools.scheduling import get_available_appointments, schedule_appointment
from servicetitan_mcp.tools.dispatching import (
    list_technicians,
    dispatch_technician,
    get_dispatch_board,
)
from servicetitan_mcp.tools.invoices import get_invoice, list_unpaid_invoices
from servicetitan_mcp.resources.docs import mcp_llms_full_resource


# ---------------------------------------------------------------------------
# Lifespan — initialize and tear down the ST API client
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Initialize ServiceTitan client on startup, close on shutdown."""
    load_dotenv()

    # Build config from env — will raise if required vars are missing
    try:
        config = ServiceTitanConfig()  # type: ignore[call-arg]
    except Exception as e:
        print(f" ServiceTitan config error: {e}")
        print("Set ST_CLIENT_ID, ST_CLIENT_SECRET, ST_APP_KEY, ST_TENANT_ID env vars.")
        print("Starting in demo mode — tools will return errors until configured.")
        yield
        return

    await init_client(config)
    print(f"ServiceTitan MCP server connected (tenant: {config.tenant_id}, env: {config.environment})")
    try:
        yield
    finally:
        await close_client()


# ---------------------------------------------------------------------------
# FastMCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "ServiceTitan MCP",
    instructions=(
        "AI-native interface to ServiceTitan for home services contractors. "
        "Supports customer lookup, job management, appointment scheduling, "
        "technician dispatching, and invoice tracking. "
        "Resource mcp-llms-full (URI: https://modelcontextprotocol.io/llms-full.txt) "
        "is the full MCP specification/docs bundle as plain text."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

mcp.add_resource(mcp_llms_full_resource())


# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

# Customers
mcp.add_tool(search_customers)
mcp.add_tool(get_customer)

# Jobs
mcp.add_tool(list_jobs)
mcp.add_tool(get_job)
mcp.add_tool(create_job)
mcp.add_tool(list_jobs_with_details)

# Scheduling
mcp.add_tool(get_available_appointments)
mcp.add_tool(schedule_appointment)

# Dispatching
mcp.add_tool(list_technicians)
mcp.add_tool(dispatch_technician)
mcp.add_tool(get_dispatch_board)

# Invoices
mcp.add_tool(get_invoice)
mcp.add_tool(list_unpaid_invoices)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
