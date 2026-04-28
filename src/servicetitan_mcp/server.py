"""ServiceTitan MCP Server — main entry point.

Exposes ServiceTitan tools via the Model Context Protocol (MCP)
using FastMCP. Supports job management, customer lookup,
scheduling, dispatching, and invoicing for home services contractors.
"""

from __future__ import annotations

import sys
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastmcp import FastMCP

from .client import init_client, close_client
from .models.types import ServiceTitanConfig
from .tools.customers import search_customers, get_customer
from .tools.jobs import list_jobs, get_job, create_job, list_jobs_with_details 
from .tools.scheduling import get_available_appointments, schedule_appointment
from .tools.dispatching import list_technicians, dispatch_technician
from .tools.invoices import get_invoice, list_unpaid_invoices



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
        "technician dispatching, and invoice tracking."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Register tools
# ---------------------------------------------------------------------------

# Customers
mcp.tool(search_customers)
mcp.tool(get_customer)

# Jobs
mcp.tool(list_jobs)
mcp.tool(get_job)
mcp.tool(create_job)

# Scheduling
mcp.tool(get_available_appointments)
mcp.tool(schedule_appointment)

# Dispatching
mcp.tool(list_technicians)
mcp.tool(dispatch_technician)

# Invoices
mcp.tool(get_invoice)
mcp.tool(list_unpaid_invoices)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
