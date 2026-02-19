"""Technician dispatching tools for ServiceTitan.

ServiceTitan APIs used:
- GET /settings/v2/tenant/{tenant}/technicians               — list technicians
- GET /settings/v2/tenant/{tenant}/technicians/{id}           — get technician
- GET /dispatch/v2/tenant/{tenant}/technician-shifts          — technician shifts/schedule
- GET /dispatch/v2/tenant/{tenant}/appointment-assignments    — who's assigned where
- POST /dispatch/v2/tenant/{tenant}/appointment-assignments   — assign tech to appointment

TODO (Day 2): The dispatch module's exact endpoints for real-time tech status
may differ. Verify against sandbox. The "technician-shifts" endpoint likely
shows scheduled shifts, not live GPS/status. Live status may require the
ServiceTitan mobile/fleet integration.
"""

from __future__ import annotations

from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError


async def list_technicians(
    active: Optional[bool] = True,
    name: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> str:
    """List active technicians with their info and current status.

    Shows technician ID, name, active status, and business unit.
    Use this to find a tech to assign to a job.

    Args:
        active: Filter by active status (default True = active only).
        name: Filter by technician name (partial match).
        page: Page number.
        page_size: Results per page (max 50).
    """
    try:
        client = get_client()
        params: dict[str, Any] = {
            "page": page,
            "pageSize": min(page_size, 50),
        }
        if active is not None:
            params["active"] = str(active).lower()
        if name:
            params["name"] = name

        result = await client.get("settings", "technicians", params=params)

        # Also try to get today's shifts for status info
        shifts = None
        try:
            from datetime import date

            today = date.today().isoformat()
            shifts = await client.get("dispatch", "technician-shifts", params={
                "startsOnOrAfter": today,
                "startsBefore": today + "T23:59:59",
                "pageSize": 200,
            })
        except Exception:
            pass

        return _format_technician_list(result, shifts)
    except ServiceTitanAPIError as e:
        return f"Error listing technicians: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def dispatch_technician(
    appointment_id: int,
    technician_id: int,
) -> str:
    """Assign or reassign a technician to a job appointment.

    This dispatches the specified technician to the given appointment.

    Args:
        appointment_id: The appointment ID to assign the technician to.
        technician_id: The technician ID to dispatch.
    """
    try:
        client = get_client()

        # TODO (Day 2): Verify the exact endpoint and body format.
        # It may be POST /dispatch/v2/tenant/{t}/appointment-assignments
        # or PUT to update existing assignment.
        body: dict[str, Any] = {
            "appointmentId": appointment_id,
            "technicianId": technician_id,
        }

        result = await client.post("dispatch", "appointment-assignments", json_body=body)

        if isinstance(result, dict):
            return (
                f"Technician {technician_id} dispatched to appointment {appointment_id} successfully."
            )
        return f"Dispatch response: {result}"
    except ServiceTitanAPIError as e:
        return f"Error dispatching technician: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_technician_list(result: Any, shifts: Any) -> str:
    if not isinstance(result, dict):
        return f"Unexpected response: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")

    if not data:
        return "No technicians found."

    # Build a shift lookup: technicianId -> shift info
    shift_map: dict[int, list[dict]] = {}
    if isinstance(shifts, dict):
        for s in shifts.get("data", []):
            tid = s.get("technicianId")
            if tid:
                shift_map.setdefault(tid, []).append(s)

    lines = [f"Technicians ({total} total):"]
    for t in data:
        tid = t.get("id", "?")
        tname = t.get("name", "Unknown")
        active = "Active" if t.get("active") else "Inactive"
        phone = t.get("phoneNumber", "")
        bu = t.get("businessUnitId", "")

        lines.append(f"\n• {tname} (ID: {tid}) — {active}")
        if phone:
            lines.append(f"  Phone: {phone}")
        if bu:
            lines.append(f"  Business Unit: {bu}")

        # Show today's shifts if available
        tech_shifts = shift_map.get(tid, [])
        if tech_shifts:
            for s in tech_shifts[:3]:
                start = str(s.get("start", ""))[:16].replace("T", " ")
                end = str(s.get("end", ""))[:16].replace("T", " ")
                lines.append(f"  Shift today: {start} – {end}")
        else:
            lines.append(f"  No shifts scheduled today")

    return "\n".join(lines)
