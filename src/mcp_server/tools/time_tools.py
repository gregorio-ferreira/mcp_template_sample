"""Time and timezone related tools."""

from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from mcp_server.utils import parse_datetime


def convert_timezone(
    dt: Annotated[str, "Datetime to convert (ISO 8601 or commonly parseable)"],
    from_tz: Annotated[str, "IANA time zone of the input (e.g., 'Europe/Madrid')"],
    to_tz: Annotated[str, "Target IANA time zone (e.g., 'America/New_York')"],
    out_format: Annotated[
        str | None,
        "Optional Python strftime format (default ISO 8601)",
    ] = None,
) -> str:
    """Convert a datetime from one IANA time zone to another.

    Returns ISO 8601 by default, or a custom strftime if provided.
    """
    aware_dt = parse_datetime(dt, assume_tz=from_tz)
    converted = aware_dt.astimezone(ZoneInfo(to_tz))
    return converted.isoformat() if not out_format else converted.strftime(out_format)


def to_unix_time(
    dt: Annotated[str, "Datetime to convert (ISO 8601, common formats, or Unix int/float)"],
    tz: Annotated[
        str | None,
        "If dt is naive (no tz info), assume this IANA time zone (default UTC)",
    ] = None,
    unit: Annotated[
        Literal["seconds", "milliseconds"],
        "Output unit (default 'seconds')",
    ] = "seconds",
) -> float:
    """Convert a timestamp string into Unix time.

    - Accepts flexible date/time strings or numeric Unix timestamps.
    - If numeric, value is returned (optionally scaled to ms).
    """
    try:
        num = float(dt)
        return num if unit == "seconds" else num * 1000.0
    except ValueError:
        pass

    aware_dt = parse_datetime(dt, assume_tz=tz)
    unix_seconds = aware_dt.timestamp()
    return unix_seconds if unit == "seconds" else unix_seconds * 1000.0
