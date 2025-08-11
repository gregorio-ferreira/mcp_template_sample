"""Tests for time tools."""

from mcp_server.tools.time_tools import convert_timezone, to_unix_time
from mcp_server.utils import parse_datetime


class TestTimezoneConversion:
    def test_basic_conversion(self) -> None:
        result = convert_timezone(
            dt="2025-08-10 09:30",
            from_tz="Europe/Madrid",
            to_tz="America/New_York",
        )
        assert "T03:30" in result or " 03:30" in result

    def test_format(self) -> None:
        result = convert_timezone(
            dt="2025-08-10T09:30:00",
            from_tz="Europe/Madrid",
            to_tz="UTC",
            out_format="%Y-%m-%d %H:%M",
        )
        assert result == "2025-08-10 07:30"


class TestUnixTime:
    def test_seconds_and_milliseconds(self) -> None:
        sec = to_unix_time("2025-08-10T09:30:00+02:00", unit="seconds")
        ms = to_unix_time("2025-08-10T09:30:00+02:00", unit="milliseconds")
        assert ms > sec
        assert abs(ms - sec * 1000) < 2

    def test_numeric_passthrough(self) -> None:
        sec = to_unix_time("1754899800", unit="seconds")
        assert abs(sec - 1754899800) < 1e-6


class TestDatetimeParser:
    def test_parse_naive_assumes_utc(self) -> None:
        dt_val = parse_datetime("2025-01-01 00:00:00")
        assert dt_val.tzinfo is not None
        offset = dt_val.utcoffset()
        assert offset is not None and offset.total_seconds() == 0

    def test_parse_with_assumed_tz(self) -> None:
        dt_val = parse_datetime("2025-01-01 00:00:00", assume_tz="Europe/Madrid")
        assert dt_val.tzinfo is not None
        assert "Madrid" in str(dt_val.tzinfo)
