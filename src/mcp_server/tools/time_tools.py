"""Time and timezone related tools."""

from zoneinfo import ZoneInfo

from mcp_server.models import TimeUnit, TimezoneConvertInput, UnixTimeInput
from mcp_server.utils import parse_datetime


def convert_timezone(data: TimezoneConvertInput) -> str:
    """Convert a datetime from one IANA time zone to another.

    Returns ISO 8601 by default, or a custom strftime if provided.
    """
    aware_dt = parse_datetime(data.dt, assume_tz=data.from_tz)
    converted = aware_dt.astimezone(ZoneInfo(data.to_tz))
    return converted.isoformat() if data.out_format is None else converted.strftime(data.out_format)


def to_unix_time(data: UnixTimeInput) -> float:
    """Convert a timestamp string into Unix time.

    - Accepts flexible date/time strings or numeric Unix timestamps.
    - If numeric, value is returned (optionally scaled to ms).
    """
    try:
        num = float(data.dt)
        return num if data.unit == TimeUnit.SECONDS else num * 1000.0
    except ValueError:
        pass

    aware_dt = parse_datetime(data.dt, assume_tz=data.tz)
    unix_seconds = aware_dt.timestamp()
    return unix_seconds if data.unit == TimeUnit.SECONDS else unix_seconds * 1000.0
