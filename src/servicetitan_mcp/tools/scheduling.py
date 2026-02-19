"""Appointment scheduling tools for ServiceTitan.

ServiceTitan Job Planning & Management (JPM) API:
- GET  /jpm/v2/tenant/{tenant}/appointments           — list appointments
- GET  /jpm/v2/tenant/{tenant}/appointments/{id}       — get appointment
- POST /jpm/v2/tenant/{tenant}/appointments            — create/schedule appointment

Job Booking (JBCE) API:
- GET /jbce/v2/tenant/{tenant}/call-reasons            — call/booking reasons

TODO (Day 2): Verify the availability-slot endpoint. ServiceTitan may use
a different mechanism (e.g., capacity planning API or booking widget API)
to expose available time slots. The current implementation queries existing
appointments and infers availability from gaps.
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError


async def get_available_appointments(
    start_date: str,
    end_date: str,
    job_type_id: Optional[int] = None,
    business_unit_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """Find available appointment slots for a job type in a given date range.

    Use this to offer scheduling options to customers. Shows existing
    appointments in the date range so you can identify open slots.

    Args:
        start_date: Start of date range (ISO 8601, e.g. "2024-03-01").
        end_date: End of date range (ISO 8601, e.g. "2024-03-07").
        job_type_id: Filter by job type to estimate duration.
        business_unit_id: Filter by business unit.
        page: Page number.
        page_size: Results per page.
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "page": page,
            "pageSize": min(page_size, 50),
            "startsOnOrAfter": start_date,
            "startsBefore": end_date,
        }
        if job_type_id:
            params["jobTypeId"] = job_type_id
        if business_unit_id:
            params["businessUnitId"] = business_unit_id

        # TODO (Day 2): ServiceTitan may have a dedicated availability/capacity
        # endpoint. For now we list scheduled appointments in the range.
        result = await client.get("jpm", "appointments", params=params)
        return _format_appointments(result, start_date, end_date)
    except ServiceTitanAPIError as e:
        return f"Error checking appointment availability: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def schedule_appointment(
    job_id: int,
    start: str,
    end: str,
    arrival_window_start: Optional[str] = None,
    arrival_window_end: Optional[str] = None,
    technician_ids: Optional[list[int]] = None,
    special_instructions: Optional[str] = None,
) -> str:
    """Schedule or reschedule an appointment for an existing job.

    Requires job ID and desired start/end times. Optionally assign
    specific technicians and set arrival window for the customer.

    Args:
        job_id: The ServiceTitan job ID.
        start: Appointment start time (ISO 8601, e.g. "2024-03-01T09:00:00").
        end: Appointment end time (ISO 8601, e.g. "2024-03-01T11:00:00").
        arrival_window_start: Customer-facing arrival window start.
        arrival_window_end: Customer-facing arrival window end.
        technician_ids: List of technician IDs to assign.
        special_instructions: Notes for the technician.
    """
    try:
        client = get_client()
        body: dict[str, Any] = {
            "jobId": job_id,
            "start": start,
            "end": end,
        }
        if arrival_window_start:
            body["arrivalWindowStart"] = arrival_window_start
        if arrival_window_end:
            body["arrivalWindowEnd"] = arrival_window_end
        if special_instructions:
            body["specialInstructions"] = special_instructions

        # TODO (Day 2): verify if technician assignment is part of appointment
        # creation or done via dispatch/appointment-assignments endpoint
        if technician_ids:
            body["technicianIds"] = technician_ids

        result = await client.post("jpm", "appointments", json_body=body)

        if isinstance(result, dict) and result.get("id"):
            appt_id = result["id"]
            return (
                f"Appointment scheduled successfully!\n"
                f"Appointment ID: {appt_id}\n"
                f"Job ID: {job_id}\n"
                f"Time: {start} — {end}"
            )
        return f"Scheduling response: {result}"
    except ServiceTitanAPIError as e:
        return f"Error scheduling appointment: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_appointments(result: Any, start_date: str, end_date: str) -> str:
    if not isinstance(result, dict):
        return f"Unexpected response: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")

    if not data:
        return f"No existing appointments found between {start_date} and {end_date}. The schedule appears open."

    lines = [f"Existing appointments between {start_date} and {end_date} ({total} total):"]
    for a in data:
        aid = a.get("id", "?")
        job_id = a.get("jobId", "?")
        status = a.get("status", "Unknown")
        start = str(a.get("start", ""))[:16].replace("T", " ")
        end = str(a.get("end", ""))[:16].replace("T", " ")

        lines.append(f"\n• Appointment {aid} (Job: {job_id}) — {status}")
        lines.append(f"  Time: {start} to {end}")

        techs = a.get("technicianIds", [])
        if techs:
            lines.append(f"  Technicians: {', '.join(str(t) for t in techs)}")

    lines.append(f"\nUse these to identify open time slots for new appointments.")
    return "\n".join(lines)
