"""Shared utilities for ServiceTitan MCP tools."""

from __future__ import annotations

from datetime import datetime, timezone, date as _date
from zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")


def _parse_st_timestamp(ts: str) -> datetime:
    """Parse a ServiceTitan timestamp, handling both UTC and tz-naive (tenant-local) formats.

    ServiceTitan returns a mix:
    - UTC with Z or +00:00 offset  → convert to Eastern
    - Explicit offset (e.g. -05:00) → convert to Eastern
    - No tz info at all             → already tenant-local (Eastern), attach tz directly
    """
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_EASTERN)
    return dt.astimezone(_EASTERN)


def to_est(ts: str | None) -> str:
    """Format a ServiceTitan timestamp as Eastern Time: '2026-05-01 09:00 AM ET'."""
    if not ts:
        return ""
    try:
        return _parse_st_timestamp(ts).strftime("%Y-%m-%d %I:%M %p ET")
    except ValueError:
        return ts


def to_est_time(ts: str | None) -> str:
    """Format a ServiceTitan timestamp as Eastern time only: '9:00 AM ET'."""
    if not ts:
        return ""
    try:
        return _parse_st_timestamp(ts).strftime("%I:%M %p ET").lstrip("0")
    except ValueError:
        return ts


def to_est_date(ts: str | None) -> str:
    """Format a ServiceTitan timestamp as Eastern date only: '2026-05-01'."""
    if not ts:
        return ""
    try:
        return _parse_st_timestamp(ts).strftime("%Y-%m-%d")
    except ValueError:
        return str(ts)[:10]


def today_est() -> str:
    """Return today's date in Eastern Time as YYYY-MM-DD."""
    return datetime.now(_EASTERN).date().isoformat()


def day_bounds_utc(date_str: str | None = None) -> tuple[str, str]:
    """Return (start, end) UTC ISO strings bounding the given Eastern date (default today)."""
    d = _date.fromisoformat(date_str) if date_str else datetime.now(_EASTERN).date()
    start_et = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=_EASTERN)
    end_et = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=_EASTERN)
    return (
        start_et.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_et.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
