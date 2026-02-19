"""Tests for ServiceTitan MCP tools.

These tests mock the ServiceTitan API client to verify tool logic
without requiring actual API credentials.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_CUSTOMER_LIST = {
    "page": 1,
    "pageSize": 25,
    "totalCount": 2,
    "hasMore": False,
    "data": [
        {
            "id": 101,
            "name": "John Smith",
            "type": "Residential",
            "active": True,
            "address": {"street": "123 Main St", "city": "Austin", "state": "TX", "zip": "78701"},
            "phoneSettings": [{"phoneNumber": "512-555-1234", "type": "Mobile"}],
        },
        {
            "id": 102,
            "name": "Jane Smith",
            "type": "Residential",
            "active": True,
            "address": {"street": "456 Oak Ave", "city": "Austin", "state": "TX", "zip": "78702"},
            "phoneSettings": [],
        },
    ],
}

MOCK_CUSTOMER_DETAIL = {
    "id": 101,
    "name": "John Smith",
    "type": "Residential",
    "active": True,
    "balance": 150.00,
    "hasActiveMembership": True,
    "address": {"street": "123 Main St", "city": "Austin", "state": "TX", "zip": "78701"},
    "createdOn": "2023-01-15T10:30:00Z",
    "doNotService": False,
}

MOCK_CUSTOMER_CONTACTS = {
    "data": [
        {"type": "Phone", "value": "512-555-1234", "memo": "Mobile"},
        {"type": "Email", "value": "john@example.com", "memo": ""},
    ]
}

MOCK_JOB_LIST = {
    "page": 1,
    "pageSize": 25,
    "totalCount": 1,
    "hasMore": False,
    "data": [
        {
            "id": 5001,
            "jobNumber": "J-5001",
            "jobStatus": "Scheduled",
            "jobTypeName": "HVAC Repair",
            "customerName": "John Smith",
            "customerId": 101,
            "createdOn": "2024-02-15T08:00:00Z",
            "totalAmount": 350.00,
        }
    ],
}

MOCK_JOB_DETAIL = {
    "id": 5001,
    "jobNumber": "J-5001",
    "jobStatus": "Scheduled",
    "jobTypeName": "HVAC Repair",
    "priority": "Normal",
    "customerName": "John Smith",
    "customerId": 101,
    "locationName": "123 Main St",
    "locationId": 201,
    "summary": "AC not cooling properly",
    "createdOn": "2024-02-15T08:00:00Z",
    "completedOn": None,
    "totalAmount": 350.00,
}

MOCK_INVOICE_DETAIL = {
    "id": 9001,
    "invoiceNumber": "INV-9001",
    "status": "Posted",
    "jobId": 5001,
    "customerName": "John Smith",
    "customerId": 101,
    "subTotal": 300.00,
    "taxAmount": 24.75,
    "total": 324.75,
    "balance": 324.75,
    "dueDate": "2024-03-15",
    "createdOn": "2024-02-20T14:00:00Z",
    "items": [
        {"description": "AC Diagnostic", "quantity": 1, "unitPrice": 100.00, "totalPrice": 100.00},
        {"description": "Refrigerant Recharge", "quantity": 1, "unitPrice": 200.00, "totalPrice": 200.00},
    ],
}

MOCK_TECHNICIAN_LIST = {
    "page": 1,
    "pageSize": 50,
    "totalCount": 2,
    "hasMore": False,
    "data": [
        {"id": 301, "name": "Mike Johnson", "active": True, "phoneNumber": "512-555-5678", "businessUnitId": 1},
        {"id": 302, "name": "Sarah Williams", "active": True, "phoneNumber": "512-555-9012", "businessUnitId": 1},
    ],
}


def _mock_client(get_responses: dict[str, Any] | None = None, post_responses: dict[str, Any] | None = None):
    """Create a mock ServiceTitanClient."""
    client = MagicMock()

    async def mock_get(module: str, endpoint: str, **kwargs) -> Any:
        key = f"{module}/{endpoint}"
        if get_responses and key in get_responses:
            return get_responses[key]
        # Default responses by module
        return {"data": [], "totalCount": 0, "hasMore": False}

    async def mock_post(module: str, endpoint: str, **kwargs) -> Any:
        key = f"{module}/{endpoint}"
        if post_responses and key in post_responses:
            return post_responses[key]
        return {"id": 1}

    client.get = mock_get
    client.post = mock_post
    return client


# ---------------------------------------------------------------------------
# Customer tool tests
# ---------------------------------------------------------------------------

class TestSearchCustomers:
    @pytest.mark.asyncio
    async def test_search_by_name(self):
        mock = _mock_client(get_responses={"crm/customers": MOCK_CUSTOMER_LIST})
        with patch("servicetitan_mcp.tools.customers.get_client", return_value=mock):
            from servicetitan_mcp.tools.customers import search_customers
            result = await search_customers(name="Smith")
            assert "John Smith" in result
            assert "Jane Smith" in result
            assert "101" in result
            assert "512-555-1234" in result

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        mock = _mock_client(get_responses={"crm/customers": {"data": [], "totalCount": 0, "hasMore": False}})
        with patch("servicetitan_mcp.tools.customers.get_client", return_value=mock):
            from servicetitan_mcp.tools.customers import search_customers
            result = await search_customers(name="Nonexistent")
            assert "No customers found" in result


class TestGetCustomer:
    @pytest.mark.asyncio
    async def test_get_customer_detail(self):
        mock = _mock_client(get_responses={
            "crm/customers/101": MOCK_CUSTOMER_DETAIL,
            "crm/customers/101/contacts": MOCK_CUSTOMER_CONTACTS,
        })
        with patch("servicetitan_mcp.tools.customers.get_client", return_value=mock):
            from servicetitan_mcp.tools.customers import get_customer
            result = await get_customer(customer_id=101)
            assert "John Smith" in result
            assert "$150.00" in result
            assert "512-555-1234" in result
            assert "john@example.com" in result


# ---------------------------------------------------------------------------
# Job tool tests
# ---------------------------------------------------------------------------

class TestListJobs:
    @pytest.mark.asyncio
    async def test_list_jobs(self):
        mock = _mock_client(get_responses={"jpm/jobs": MOCK_JOB_LIST})
        with patch("servicetitan_mcp.tools.jobs.get_client", return_value=mock):
            from servicetitan_mcp.tools.jobs import list_jobs
            result = await list_jobs(status="Scheduled")
            assert "J-5001" in result
            assert "Scheduled" in result
            assert "HVAC Repair" in result


class TestGetJob:
    @pytest.mark.asyncio
    async def test_get_job_detail(self):
        mock = _mock_client(get_responses={
            "jpm/jobs/5001": MOCK_JOB_DETAIL,
            "jpm/jobs/5001/notes": {"data": [{"text": "Customer prefers morning", "createdOn": "2024-02-15"}]},
        })
        with patch("servicetitan_mcp.tools.jobs.get_client", return_value=mock):
            from servicetitan_mcp.tools.jobs import get_job
            result = await get_job(job_id=5001)
            assert "J-5001" in result
            assert "AC not cooling" in result
            assert "Customer prefers morning" in result


class TestCreateJob:
    @pytest.mark.asyncio
    async def test_create_job_success(self):
        mock = _mock_client(post_responses={"jpm/jobs": {"id": 5002, "jobNumber": "J-5002"}})
        with patch("servicetitan_mcp.tools.jobs.get_client", return_value=mock):
            from servicetitan_mcp.tools.jobs import create_job
            result = await create_job(customer_id=101, location_id=201, job_type_id=10)
            assert "5002" in result
            assert "successfully" in result.lower()


# ---------------------------------------------------------------------------
# Invoice tool tests
# ---------------------------------------------------------------------------

class TestGetInvoice:
    @pytest.mark.asyncio
    async def test_get_invoice_detail(self):
        mock = _mock_client(get_responses={"accounting/invoices/9001": MOCK_INVOICE_DETAIL})
        with patch("servicetitan_mcp.tools.invoices.get_client", return_value=mock):
            from servicetitan_mcp.tools.invoices import get_invoice
            result = await get_invoice(invoice_id=9001)
            assert "INV-9001" in result
            assert "$324.75" in result
            assert "AC Diagnostic" in result
            assert "UNPAID" in result


# ---------------------------------------------------------------------------
# Technician tool tests
# ---------------------------------------------------------------------------

class TestListTechnicians:
    @pytest.mark.asyncio
    async def test_list_technicians(self):
        mock = _mock_client(get_responses={
            "settings/technicians": MOCK_TECHNICIAN_LIST,
        })
        # Mock the dispatch call to raise so we test the fallback
        original_get = mock.get

        async def patched_get(module, endpoint, **kwargs):
            if module == "dispatch":
                raise Exception("Not available")
            return await original_get(module, endpoint, **kwargs)

        mock.get = patched_get

        with patch("servicetitan_mcp.tools.dispatching.get_client", return_value=mock):
            from servicetitan_mcp.tools.dispatching import list_technicians
            result = await list_technicians()
            assert "Mike Johnson" in result
            assert "Sarah Williams" in result
            assert "301" in result
