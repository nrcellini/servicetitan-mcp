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

import asyncio
from typing import Any, Optional

from ..client import get_client, ServiceTitanAPIError
from ..utils import to_est, to_est_time, today_est, day_bounds_utc


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

        today = today_est()
        day_start, day_end = day_bounds_utc(today)

        result, shifts = await asyncio.gather(
            client.get("settings", "technicians", params=params),
            _fetch_shifts(client, day_start, day_end),
        )

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

        body: dict[str, Any] = {
            "appointmentId": appointment_id,
            "technicianId": technician_id,
        }

        result = await client.post("dispatch", "appointment-assignments", json_body=body)

        if isinstance(result, dict):
            return f"Technician {technician_id} dispatched to appointment {appointment_id} successfully."
        return f"Dispatch response: {result}"
    except ServiceTitanAPIError as e:
        return f"Error dispatching technician: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


async def get_dispatch_board(date: Optional[str] = None) -> str:
    """Get the current dispatch board snapshot for a given date (default: today EST).

    Shows every active technician with their shift window, each assigned appointment,
    job type, customer name, service address, and appointment status — all in one call.
    Also lists any unassigned appointments so nothing falls through the cracks.

    Args:
        date: Date to view in YYYY-MM-DD format (default: today in Eastern Time).
    """
    try:
        client = get_client()
        target_date = date or today_est()
        day_start, day_end = day_bounds_utc(target_date)

        # Round 1: techs, shifts, and appointments for the day in parallel
        techs_resp, shifts, appts_resp = await asyncio.gather(
            client.get("settings", "technicians", params={"active": "true", "pageSize": 200}),
            _fetch_shifts(client, day_start, day_end),
            client.get("jpm", "appointments", params={
                "startsOnOrAfter": day_start,
                "startsBefore": day_end,
                "pageSize": 200,
            }),
        )

        techs: list[dict] = techs_resp.get("data", []) if isinstance(techs_resp, dict) else []
        appts: list[dict] = appts_resp.get("data", []) if isinstance(appts_resp, dict) else []

        appt_ids = {a["id"] for a in appts if a.get("id")}
        job_ids = {a["jobId"] for a in appts if a.get("jobId")}

        # Round 2: assignments and jobs in parallel
        assignments, jobs_resp = await asyncio.gather(
            _fetch_assignments(client, appt_ids),
            _fetch_jobs_by_ids(client, job_ids),
        )

        location_ids = {j["locationId"] for j in jobs_resp if j.get("locationId")}

        # Round 3: locations
        locations_resp = await client.get("crm", "locations", params={
            "ids": ",".join(str(i) for i in location_ids),
            "pageSize": 200,
        }) if location_ids else {"data": []}
        locations: list[dict] = locations_resp.get("data", []) if isinstance(locations_resp, dict) else []

        # Build lookup maps
        shift_by_tech: dict[int, list[dict]] = {}
        for s in shifts:
            tid = s.get("technicianId")
            if tid:
                shift_by_tech.setdefault(tid, []).append(s)

        appt_map = {a["id"]: a for a in appts}
        appts_by_tech: dict[int, list[dict]] = {}
        assigned_appt_ids: set[int] = set()
        for a in assignments:
            tid = a.get("technicianId")
            aid = a.get("appointmentId")
            if tid and aid:
                assigned_appt_ids.add(aid)
                if aid in appt_map:
                    appts_by_tech.setdefault(tid, []).append(appt_map[aid])

        job_map = {j["id"]: j for j in jobs_resp}
        loc_map = {l["id"]: l for l in locations}

        # Format the board
        lines = [f"Dispatch Board — {target_date}", "=" * 50]

        active_tech_ids = set(shift_by_tech) | set(appts_by_tech)
        sorted_techs = sorted(
            [t for t in techs if t["id"] in active_tech_ids],
            key=lambda t: t.get("name", ""),
        )

        for tech in sorted_techs:
            tid = tech["id"]
            tname = tech.get("name", "Unknown")
            lines.append(f"\n● {tname} (ID: {tid})")

            for s in shift_by_tech.get(tid, []):
                lines.append(f"  Shift: {to_est_time(s.get('start'))} – {to_est_time(s.get('end'))}")

            tech_appts = sorted(appts_by_tech.get(tid, []), key=lambda a: a.get("start", ""))
            if tech_appts:
                for appt in tech_appts:
                    job = job_map.get(appt.get("jobId"), {})
                    loc = loc_map.get(job.get("locationId"), {})
                    addr = loc.get("address", {})
                    addr_str = ", ".join(filter(None, [
                        addr.get("street"),
                        addr.get("city"),
                        addr.get("state"),
                    ])) if addr else loc.get("name", "")

                    lines.append(
                        f"  [{to_est_time(appt.get('start'))} – {to_est_time(appt.get('end'))}]"
                        f"  Job #{job.get('jobNumber', '?')} • {job.get('jobTypeName', '?')}"
                    )
                    lines.append(f"    Customer: {job.get('customerName', '?')}")
                    if addr_str:
                        lines.append(f"    Address:  {addr_str}")
                    lines.append(f"    Status:   {appt.get('status', '?')}")
            else:
                lines.append("  No appointments assigned")

        # Unassigned appointments
        unassigned = [a for a in appts if a.get("id") not in assigned_appt_ids]
        if unassigned:
            lines.append(f"\n⚠ UNASSIGNED ({len(unassigned)}):")
            for appt in sorted(unassigned, key=lambda a: a.get("start", "")):
                job = job_map.get(appt.get("jobId"), {})
                loc = loc_map.get(job.get("locationId"), {})
                addr = loc.get("address", {})
                addr_str = ", ".join(filter(None, [addr.get("street"), addr.get("city")])) if addr else ""
                lines.append(
                    f"  [{to_est_time(appt.get('start'))}]"
                    f"  Job #{job.get('jobNumber','?')} • {job.get('jobTypeName','?')}"
                    f" — {job.get('customerName','?')}"
                )
                if addr_str:
                    lines.append(f"    {addr_str}")

        if len(lines) <= 2:
            return f"No dispatch activity found for {target_date}."

        return "\n".join(lines)
    except ServiceTitanAPIError as e:
        return f"Error fetching dispatch board: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _fetch_shifts(client, day_start: str, day_end: str) -> list[dict]:
    try:
        resp = await client.get("dispatch", "technician-shifts", params={
            "startsOnOrAfter": day_start,
            "startsBefore": day_end,
            "pageSize": 200,
        })
        return resp.get("data", []) if isinstance(resp, dict) else []
    except Exception:
        return []


async def _fetch_assignments(client, appt_ids: set[int]) -> list[dict]:
    if not appt_ids:
        return []
    resp = await client.get("dispatch", "appointment-assignments", params={
        "appointmentIds": ",".join(str(i) for i in appt_ids),
        "active": "true",
        "pageSize": 200,
    })
    return resp.get("data", []) if isinstance(resp, dict) else []


async def _fetch_jobs_by_ids(client, job_ids: set[int]) -> list[dict]:
    if not job_ids:
        return []
    resp = await client.get("jpm", "jobs", params={
        "ids": ",".join(str(i) for i in job_ids),
        "pageSize": 200,
    })
    return resp.get("data", []) if isinstance(resp, dict) else []


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_technician_list(result: Any, shifts: list[dict]) -> str:
    if not isinstance(result, dict):
        return f"Unexpected response: {result}"

    data = result.get("data", [])
    total = result.get("totalCount", "?")

    if not data:
        return "No technicians found."

    shift_map: dict[int, list[dict]] = {}
    for s in shifts:
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

        tech_shifts = shift_map.get(tid, [])
        if tech_shifts:
            for s in tech_shifts[:3]:
                lines.append(f"  Shift today: {to_est_time(s.get('start'))} – {to_est_time(s.get('end'))}")
        else:
            lines.append("  No shifts scheduled today")

    return "\n".join(lines)
