"""Utility functions for the MCP server."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from dateutil import parser as dateutil_parser


def parse_datetime(dt: str, assume_tz: str | None = None) -> datetime:
    """Parse a wide range of datetime strings into an aware datetime.

    - Accepts ISO 8601, 'YYYY-MM-DD HH:MM', 'YYYY/MM/DD HH:MM:SS', etc.
    - Accepts 'Z' suffix for UTC.
    - If parsed datetime is naive and `assume_tz` provided, localize to that IANA tz.
    - If parsed datetime is naive and no assume_tz, treat it as UTC.
    """
    parsed = dateutil_parser.parse(dt)
    if parsed.tzinfo is None:
        if assume_tz:
            parsed = parsed.replace(tzinfo=ZoneInfo(assume_tz))
        else:
            parsed = parsed.replace(tzinfo=UTC)
    return parsed
