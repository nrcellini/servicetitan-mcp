"""Job management tools for ServiceTitan.

ServiceTitan Job Planning & Management (JPM) API:
- GET  /jpm/v2/tenant/{tenant}/jobs              — list jobs
- GET  /jpm/v2/tenant/{tenant}/jobs/{id}          — get job by ID
- POST /jpm/v2/tenant/{tenant}/jobs               — create a job
- GET  /jpm/v2/tenant/{tenant}/jobs/{id}/notes     — get job notes
- GET  /jpm/v2/tenant/{tenant}/jobs/{id}/history   — get job history
- GET  /jpm/v2/tenant/{tenant}/job-types           — list job types
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError


async def list_jobs(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    technician_id: Optional[int] = None,
    job_type_id: Optional[int] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    completed_after: Optional[str] = None,
    completed_before: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_direction: Optional[str] = None,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """List jobs in ServiceTitan with optional filters for status, date range, customer, or technician.

    Returns job ID, type, status, scheduled time, and assigned tech.

    Args:
        status: Filter by job status — Scheduled, InProgress, Completed, Canceled, Hold.
        customer_id: Filter by customer ID.
        technician_id: Filter by assigned technician ID.
        job_type_id: Filter by job type ID.
        created_after: Only jobs created after this date (ISO 8601, e.g. "2024-01-01").
        created_before: Only jobs created before this date.
        completed_after: Only jobs completed after this date.
        completed_before: Only jobs completed before this date.
        sort_by: Field to sort by (e.g. "createdOn", "modifiedOn").
        sort_direction: "asc" or "desc".
        page: Page number.
        page_size: Results per page (max 50).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "page": page,
            "pageSize": min(page_size, 50),
        }
        if status:
            params["jobStatus"] = status
        if customer_id:
            params["customerId"] = customer_id
        if technician_id:
            # TODO: verify param name — may be technicianId or assignedTechnicianId
            params["technicianId"] = technician_id
        if job_type_id:
            params["jobTypeId"] = job_type_id
        if created_after:
            params["createdOnOrAfter"] = created_after
        if created_before:
            params["createdBefore"] = created_before
        if completed_after:
            params["completedOnOrAfter"] = completed_after
        if completed_before:
            params["completedBefore"] = completed_before
        if sort_by:
            params["orderBy"] = sort_by
        if sort_direction:
            params["orderByDirection"] = sort_direction

        result = await client.get("jpm", "jobs", params=params)
        return _format_job_list(result)
    except ServiceTitanAPIError as e:
        return f"Error listing jobs: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def get_job(job_id: int) -> str:
    """Get complete details for a specific job including customer info, assigned technician, scheduled time, job notes, and current status.

    Args:
        job_id: The ServiceTitan job ID.
    """
    try:
        client = get_client()
        job = await client.get("jpm", f"jobs/{job_id}")

        # Fetch notes too
        try:
            notes = await client.get("jpm", f"jobs/{job_id}/notes")
        except Exception:
            notes = None

        return _format_job_detail(job, notes)
    except ServiceTitanAPIError as e:
        return f"Error fetching job {job_id}: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def create_job(
    customer_id: int,
    location_id: int,
    job_type_id: int,
    summary: Optional[str] = None,
    priority: Optional[str] = None,
    business_unit_id: Optional[int] = None,
    campaign_id: Optional[int] = None,
) -> str:
    """Create a new job in ServiceTitan for a customer.

    Requires customer ID, location ID, and job type. Returns the new job ID.
    Use search_customers first to find the customer ID, and list available
    job types if unsure which job_type_id to use.

    Args:
        customer_id: The ServiceTitan customer ID.
        location_id: The service location ID for this customer.
        job_type_id: The job type ID (use list_job_types to find available types).
        summary: Optional job description/summary.
        priority: Job priority — Normal, High, Urgent (default Normal).
        business_unit_id: Business unit ID (if applicable).
        campaign_id: Marketing campaign ID (if applicable).
    """
    try:
        client = get_client()
        body: dict[str, Any] = {
            "customerId": customer_id,
            "locationId": location_id,
            "jobTypeId": job_type_id,
        }
        if summary:
            body["summary"] = summary
        if priority:
            body["priority"] = priority
        if business_unit_id:
            body["businessUnitId"] = business_unit_id
        if campaign_id:
            body["campaignId"] = campaign_id

        # TODO (Day 2): verify POST body schema against sandbox
        result = await client.post("jpm", "jobs", json_body=body)

        if isinstance(result, dict) and result.get("id"):
            return f"Job created successfully! Job ID: {result['id']}, Number: {result.get('jobNumber', 'N/A')}"
        return f"Job creation response: {result}"
    except ServiceTitanAPIError as e:
        return f"Error creating job: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_job_list(result: Any) -> str:
    if not isinstance(result, dict):
        return f"Unexpected response: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")
    has_more = result.get("hasMore", False)

    if not data:
        return "No jobs found matching your filters."

    lines = [f"Found {total} job(s):"]
    for j in data:
        jid = j.get("id", "?")
        num = j.get("jobNumber", "")
        status = j.get("jobStatus", "Unknown")
        jtype = j.get("jobTypeName", j.get("jobTypeId", "N/A"))
        customer = j.get("customerName", j.get("customerId", "N/A"))
        created = str(j.get("createdOn", ""))[:10]

        lines.append(f"\n• Job #{num} (ID: {jid}) — {status}")
        lines.append(f"  Type: {jtype} | Customer: {customer}")
        lines.append(f"  Created: {created}")

        total_amt = j.get("totalAmount")
        if total_amt is not None:
            lines.append(f"  Total: ${total_amt:.2f}")

    if has_more:
        lines.append(f"\n(More results available — request next page)")

    return "\n".join(lines)


def _format_job_detail(job: Any, notes: Any) -> str:
    if not isinstance(job, dict):
        return f"Unexpected response: {job}"

    lines = [
        f"Job #{job.get('jobNumber', '?')} (ID: {job.get('id', '?')})",
        f"Status: {job.get('jobStatus', 'Unknown')}",
        f"Type: {job.get('jobTypeName', job.get('jobTypeId', 'N/A'))}",
        f"Priority: {job.get('priority', 'Normal')}",
        f"Customer: {job.get('customerName', 'N/A')} (ID: {job.get('customerId', '?')})",
        f"Location: {job.get('locationName', 'N/A')} (ID: {job.get('locationId', '?')})",
        f"Summary: {job.get('summary', 'N/A')}",
        f"Created: {job.get('createdOn', 'N/A')}",
        f"Completed: {job.get('completedOn', 'N/A')}",
    ]

    total_amt = job.get("totalAmount")
    if total_amt is not None:
        lines.append(f"Total Amount: ${total_amt:.2f}")

    # Notes
    note_data = None
    if isinstance(notes, dict):
        note_data = notes.get("data", [])
    elif isinstance(notes, list):
        note_data = notes

    if note_data:
        lines.append(f"\nNotes ({len(note_data)}):")
        for n in note_data[:10]:  # Limit to most recent 10
            text = n.get("text", "")[:200]
            date = str(n.get("createdOn", ""))[:10]
            lines.append(f"  [{date}] {text}")

    return "\n".join(lines)
