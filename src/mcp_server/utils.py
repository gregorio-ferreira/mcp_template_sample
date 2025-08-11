"""Utility functions for the MCP server."""

import logging
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def parse_datetime(dt: str, assume_tz: Optional[str] = None) -> datetime:
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
            parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def setup_logging(level: str = "INFO") -> None:
    """Setup structured logging for the server."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
