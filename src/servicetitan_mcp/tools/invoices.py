"""Invoice tools for ServiceTitan.

ServiceTitan Accounting API:
- GET /accounting/v2/tenant/{tenant}/invoices              — list invoices
- GET /accounting/v2/tenant/{tenant}/invoices/{id}          — get invoice by ID
- GET /accounting/v2/tenant/{tenant}/export/invoice-items   — export invoice line items

TODO (Day 2): Verify invoice filtering params (e.g., unpaid status filter,
customer filter). The "balance" field on invoices may indicate unpaid amount.
ServiceTitan may also have a payments endpoint for payment status.
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError


async def get_invoice(invoice_id: int) -> str:
    """Get invoice details for a job including line items, total amount, payment status, and due date.

    Args:
        invoice_id: The ServiceTitan invoice ID.
    """
    try:
        client = get_client()
        invoice = await client.get("accounting", f"invoices/{invoice_id}")
        return _format_invoice_detail(invoice)
    except ServiceTitanAPIError as e:
        return f"Error fetching invoice {invoice_id}: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def list_unpaid_invoices(
    customer_id: Optional[int] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    min_balance: Optional[float] = None,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """List all unpaid or overdue invoices, optionally filtered by customer or date range.

    Useful for collections follow-up and accounts receivable management.

    Args:
        customer_id: Filter by customer ID.
        created_after: Only invoices created after this date (ISO 8601).
        created_before: Only invoices created before this date.
        min_balance: Minimum outstanding balance to include.
        page: Page number.
        page_size: Results per page (max 50).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "page": page,
            "pageSize": min(page_size, 50),
        }
        if customer_id:
            params["customerId"] = customer_id
        if created_after:
            params["createdOnOrAfter"] = created_after
        if created_before:
            params["createdBefore"] = created_before
        # TODO (Day 2): verify if there's a direct "unpaid" or "balance > 0" filter.
        # We may need to fetch all and filter client-side, or use export endpoint.

        result = await client.get("accounting", "invoices", params=params)

        # Client-side filter for unpaid (balance > 0)
        if isinstance(result, dict) and result.get("data"):
            unpaid = [
                inv for inv in result["data"]
                if (inv.get("balance") or 0) > (min_balance or 0)
            ]
            result = dict(result)
            result["data"] = unpaid
            result["totalCount"] = len(unpaid)

        return _format_invoice_list(result, unpaid_only=True)
    except ServiceTitanAPIError as e:
        return f"Error listing invoices: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_invoice_detail(invoice: Any) -> str:
    if not isinstance(invoice, dict):
        return f"Unexpected response: {invoice}"

    lines = [
        f"Invoice #{invoice.get('invoiceNumber', '?')} (ID: {invoice.get('id', '?')})",
        f"Status: {invoice.get('status', 'Unknown')}",
        f"Job ID: {invoice.get('jobId', 'N/A')}",
        f"Customer: {invoice.get('customerName', 'N/A')} (ID: {invoice.get('customerId', '?')})",
        f"Subtotal: ${invoice.get('subTotal', 0):.2f}",
        f"Tax: ${invoice.get('taxAmount', 0):.2f}",
        f"Total: ${invoice.get('total', 0):.2f}",
        f"Balance Due: ${invoice.get('balance', 0):.2f}",
        f"Due Date: {invoice.get('dueDate', 'N/A')}",
        f"Created: {invoice.get('createdOn', 'N/A')}",
    ]

    # Line items
    items = invoice.get("items", [])
    if items:
        lines.append(f"\nLine Items ({len(items)}):")
        for item in items:
            desc = item.get("description", item.get("skuName", "Unknown"))
            qty = item.get("quantity", 1)
            unit_price = item.get("unitPrice", 0)
            total_price = item.get("totalPrice", 0)
            lines.append(f"  • {desc}: {qty} × ${unit_price:.2f} = ${total_price:.2f}")

    payment_status = "PAID" if (invoice.get("balance") or 0) <= 0 else "UNPAID"
    lines.append(f"\nPayment Status: {payment_status}")

    return "\n".join(lines)


def _format_invoice_list(result: Any, unpaid_only: bool = False) -> str:
    if not isinstance(result, dict):
        return f"Unexpected response: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")

    label = "unpaid invoice" if unpaid_only else "invoice"
    if not data:
        return f"No {label}s found matching your criteria."

    total_outstanding = sum(inv.get("balance", 0) for inv in data if inv.get("balance"))

    lines = [f"Found {total} {label}(s) — Total outstanding: ${total_outstanding:.2f}"]
    for inv in data:
        inv_id = inv.get("id", "?")
        num = inv.get("invoiceNumber", "")
        status = inv.get("status", "Unknown")
        customer = inv.get("customerName", inv.get("customerId", "N/A"))
        total_amt = inv.get("total", 0)
        balance = inv.get("balance", 0)
        created = str(inv.get("createdOn", ""))[:10]
        due = str(inv.get("dueDate", ""))[:10] if inv.get("dueDate") else "N/A"

        lines.append(f"\n• Invoice #{num} (ID: {inv_id}) — {status}")
        lines.append(f"  Customer: {customer}")
        lines.append(f"  Total: ${total_amt:.2f} | Balance: ${balance:.2f}")
        lines.append(f"  Created: {created} | Due: {due}")

    return "\n".join(lines)
