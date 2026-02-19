"""Customer lookup and detail tools for ServiceTitan.

ServiceTitan CRM API:
- GET /crm/v2/tenant/{tenant}/customers          — list/search customers
- GET /crm/v2/tenant/{tenant}/customers/{id}      — get customer by ID
- GET /crm/v2/tenant/{tenant}/customers/{id}/contacts — get customer contacts
- GET /crm/v2/tenant/{tenant}/customers/{id}/notes    — get customer notes
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError


async def search_customers(
    name: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    active: Optional[bool] = True,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """Search ServiceTitan customers by name, phone number, email, or address.

    Returns customer ID, name, contact info, and service address.
    Use this before creating a job to find the right customer.

    Args:
        name: Customer name to search (partial match).
        phone: Phone number to search.
        email: Email address to search.
        street: Street address filter.
        city: City filter.
        state: State/province filter.
        zip_code: ZIP/postal code filter.
        active: Only return active customers (default True).
        page: Page number for pagination.
        page_size: Results per page (max 50).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "page": page,
            "pageSize": min(page_size, 50),
        }
        if name:
            params["name"] = name
        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email
        if street:
            params["street"] = street
        if city:
            params["city"] = city
        if state:
            params["state"] = state
        if zip_code:
            params["zip"] = zip_code
        if active is not None:
            params["active"] = str(active).lower()

        result = await client.get("crm", "customers", params=params)
        return _format_customer_list(result)
    except ServiceTitanAPIError as e:
        return f"Error searching customers: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def get_customer(customer_id: int) -> str:
    """Get full details for a specific ServiceTitan customer including contact info and service history summary.

    Args:
        customer_id: The ServiceTitan customer ID.
    """
    try:
        client = get_client()
        customer = await client.get("crm", f"customers/{customer_id}")

        # Also fetch contacts for this customer
        try:
            contacts = await client.get("crm", f"customers/{customer_id}/contacts")
        except Exception:
            contacts = None

        return _format_customer_detail(customer, contacts)
    except ServiceTitanAPIError as e:
        return f"Error fetching customer {customer_id}: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Formatting helpers — produce LLM-friendly text output
# ---------------------------------------------------------------------------

def _format_customer_list(result: Any) -> str:
    """Format paginated customer list into readable text."""
    if not isinstance(result, dict):
        return f"Unexpected response format: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")
    has_more = result.get("hasMore", False)

    if not data:
        return "No customers found matching your search criteria."

    lines = [f"Found {total} customer(s):"]
    for c in data:
        cid = c.get("id", "?")
        cname = c.get("name", "Unknown")
        ctype = c.get("type", "")
        active = "Active" if c.get("active") else "Inactive"
        addr = c.get("address", {})
        addr_str = ""
        if isinstance(addr, dict):
            parts = [addr.get("street", ""), addr.get("city", ""), addr.get("state", ""), addr.get("zip", "")]
            addr_str = ", ".join(p for p in parts if p)

        lines.append(f"\n• ID: {cid} | {cname} ({ctype}, {active})")
        if addr_str:
            lines.append(f"  Address: {addr_str}")

        # Show first phone if available
        phone_settings = c.get("phoneSettings", [])
        if phone_settings and isinstance(phone_settings, list):
            for ps in phone_settings[:2]:
                lines.append(f"  Phone: {ps.get('phoneNumber', 'N/A')} ({ps.get('type', '')})")

    if has_more:
        lines.append(f"\n(More results available — request next page)")

    return "\n".join(lines)


def _format_customer_detail(customer: Any, contacts: Any) -> str:
    """Format a single customer detail into readable text."""
    if not isinstance(customer, dict):
        return f"Unexpected response: {customer}"

    lines = [f"Customer: {customer.get('name', 'Unknown')} (ID: {customer.get('id', '?')})"]
    lines.append(f"Type: {customer.get('type', 'N/A')}")
    lines.append(f"Active: {'Yes' if customer.get('active') else 'No'}")
    lines.append(f"Balance: ${customer.get('balance', 0):.2f}")
    lines.append(f"Membership: {'Active' if customer.get('hasActiveMembership') else 'None'}")

    addr = customer.get("address", {})
    if isinstance(addr, dict):
        parts = [addr.get("street", ""), addr.get("city", ""), addr.get("state", ""), addr.get("zip", "")]
        addr_str = ", ".join(p for p in parts if p)
        if addr_str:
            lines.append(f"Address: {addr_str}")

    lines.append(f"Created: {customer.get('createdOn', 'N/A')}")
    lines.append(f"Do Not Service: {'Yes' if customer.get('doNotService') else 'No'}")

    # Contacts
    contact_data = None
    if isinstance(contacts, dict):
        contact_data = contacts.get("data", [])
    elif isinstance(contacts, list):
        contact_data = contacts

    if contact_data:
        lines.append("\nContacts:")
        for ct in contact_data:
            lines.append(f"  • {ct.get('type', 'Unknown')}: {ct.get('value', 'N/A')} {ct.get('memo', '')}")

    return "\n".join(lines)
