"""Pydantic models for type safety and validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TimeUnit(str, Enum):
    """Time unit enumeration."""

    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"


class TimezoneConvertInput(BaseModel):
    """Input model for timezone conversion."""

    dt: str = Field(
        ...,
        examples=["2025-08-10 09:30", "2025-08-10T09:30:00", "2025-08-10T09:30:00Z"],
        description="Datetime to convert (various common formats).",
    )
    from_tz: str = Field(
        ...,
        examples=["Europe/Madrid", "America/New_York", "Asia/Tokyo"],
        description="Source IANA timezone.",
    )
    to_tz: str = Field(
        ...,
        examples=["America/New_York", "Europe/London", "UTC"],
        description="Target IANA timezone.",
    )
    out_format: Optional[str] = Field(
        None,
        examples=["%Y-%m-%d %H:%M", "%d/%m/%Y %I:%M %p"],
        description="Optional strftime format; if omitted returns ISO 8601.",
    )

    @field_validator("from_tz", "to_tz")
    @classmethod
    def validate_timezone(cls, v: str) -> str:  # pragma: no cover - simple placeholder
        """Validate IANA timezone names (placeholder)."""
        # Could integrate with zoneinfo.available_timezones() for stricter validation.
        return v


class UnixTimeInput(BaseModel):
    """Input model for Unix time conversion."""

    dt: str = Field(
        ...,
        examples=["2025-08-10T09:30:00+02:00", "2025-08-10 09:30", "1754899800"],
        description="Datetime (string) or numeric unix timestamp to convert.",
    )
    tz: Optional[str] = Field(
        None,
        examples=["Europe/Madrid", "America/New_York"],
        description="Assumed IANA timezone if dt is naive; default UTC.",
    )
    unit: TimeUnit = Field(
        default=TimeUnit.SECONDS,
        description="Desired output unit (seconds or milliseconds).",
    )


class ServerConfig(BaseModel):
    """Server configuration model."""

    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    path: str = Field(default="/mcp", description="HTTP path prefix for MCP")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")


class ToolResult(BaseModel):
    """Standard tool result model."""

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
