# MCP Server Python Project Template

## Project Structure

```
mcp-server-template/
├── pyproject.toml
├── README.md
├── .gitignore
├── .env.example
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py           # Main server that registers tools
│       ├── models.py           # Pydantic models for type safety
│       ├── config.py           # Configuration management
│       ├── utils.py            # Utility functions
│       └── tools/              # Tool implementations directory
│           ├── __init__.py
│           ├── time_tools.py   # Time-related tools
│           ├── file_tools.py   # File manipulation tools (example)
│           └── data_tools.py   # Data processing tools (example)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_server.py         # Server tests
│   └── test_tools/            # Tool-specific tests
│       ├── __init__.py
│       ├── test_time_tools.py
│       ├── test_file_tools.py
│       └── test_data_tools.py
├── examples/
│   ├── agent_client.py        # Example LangGraph agent
│   └── simple_client.py       # Simple client example
└── scripts/
    ├── run_server.py          # Server startup script
    └── validate_server.py     # Validation script
```

## File Contents

### pyproject.toml

```toml
[project]
name = "mcp-server-template"
version = "0.1.0"
description = "A template for building MCP servers with FastMCP"
readme = "README.md"
requires-python = ">=3.13"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
license = { text = "MIT" }
keywords = ["mcp", "model-context-protocol", "fastmcp", "ai", "llm"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "fastmcp>=2.0",
    "pydantic>=2.5",
    "python-dateutil>=2.9",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "mypy>=1.8",
    "ruff>=0.3",
    "pre-commit>=3.6",
]

agent = [
    "langchain-mcp-adapters>=0.1.9",
    "langgraph>=0.2",
    "langchain[openai]>=0.1",
]

[project.scripts]
mcp-server = "mcp_server.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "mypy>=1.8",
    "ruff>=0.3",
    "ipython>=8.20",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--strict-markers",
    "--cov=src/mcp_server",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
no_implicit_reexport = true
namespace_packages = true
show_error_codes = true
show_column_numbers = true
pretty = true

[[tool.mypy.overrides]]
module = [
    "mcp.*",
    "langchain.*",
    "langgraph.*",
]
ignore_missing_imports = true

[tool.ruff]
target-version = "py313"
line-length = 100
fix = true

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "ARG",  # flake8-unused-arguments
    "SIM",  # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### src/mcp_server/__init__.py

```python
"""MCP Server Template Package."""

from mcp_server.models import TimezoneConvertInput, UnixTimeInput, ToolResult

__version__ = "0.1.0"
__all__ = ["TimezoneConvertInput", "UnixTimeInput", "ToolResult"]
```

### src/mcp_server/models.py

```python
"""Pydantic models for type safety and validation."""

from __future__ import annotations

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
        description="Datetime to convert (ISO 8601 or commonly parseable)",
        examples=["2025-08-10 09:30", "2025-08-10T09:30:00", "2025-08-10T09:30:00Z"],
    )
    from_tz: str = Field(
        ...,
        description="IANA time zone of the input",
        examples=["Europe/Madrid", "America/New_York", "Asia/Tokyo"],
    )
    to_tz: str = Field(
        ...,
        description="Target IANA time zone",
        examples=["America/New_York", "Europe/London", "UTC"],
    )
    out_format: Optional[str] = Field(
        None,
        description="Optional Python strftime format (default ISO 8601)",
        examples=["%Y-%m-%d %H:%M", "%d/%m/%Y %I:%M %p"],
    )

    @field_validator("from_tz", "to_tz")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate IANA timezone names."""
        from zoneinfo import available_timezones
        
        if v not in available_timezones():
            # Allow common aliases
            aliases = {"UTC": "UTC", "GMT": "GMT"}
            if v in aliases:
                return aliases[v]
            raise ValueError(f"Invalid timezone: {v}")
        return v


class UnixTimeInput(BaseModel):
    """Input model for Unix time conversion."""
    
    dt: str = Field(
        ...,
        description="Datetime to convert (ISO 8601, common formats, or Unix timestamp)",
        examples=["2025-08-10T09:30:00+02:00", "2025-08-10 09:30", "1754899800"],
    )
    tz: Optional[str] = Field(
        None,
        description="If dt is naive (no tz info), assume this IANA time zone (default UTC)",
        examples=["Europe/Madrid", "America/New_York"],
    )
    unit: TimeUnit = Field(
        TimeUnit.SECONDS,
        description="Output unit",
    )


class ServerConfig(BaseModel):
    """Server configuration model."""
    
    host: str = Field("127.0.0.1", description="Server host")
    port: int = Field(8000, description="Server port", ge=1, le=65535)
    path: str = Field("/mcp", description="MCP endpoint path")
    debug: bool = Field(False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Logging level"
    )
    
    class Config:
        """Pydantic config."""
        
        env_prefix = "MCP_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class ToolResult(BaseModel):
    """Standard tool result model."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    data: Any = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
```

### src/mcp_server/core/config.py

```python
"""Configuration management for the MCP server."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from mcp_server.models import ServerConfig


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        load_dotenv(env_file)


@lru_cache(maxsize=1)
def get_config() -> ServerConfig:
    """
    Get server configuration (singleton pattern).
    
    Returns:
        ServerConfig: Validated server configuration
        
    Raises:
        ValidationError: If configuration is invalid
    """
    load_environment()
    
    try:
        config = ServerConfig(
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
            path=os.getenv("MCP_PATH", "/mcp"),
            debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
        )
    except ValidationError as e:
        print(f"Configuration error: {e}")
        raise
    
    return config
```

### src/mcp_server/utils.py

```python
"""Utility functions for the MCP server."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser
from zoneinfo import ZoneInfo


def parse_datetime(dt: str, assume_tz: Optional[str] = None) -> datetime:
    """
    Parse a wide range of datetime strings into an aware datetime.

    Args:
        dt: Datetime string to parse
        assume_tz: Optional IANA timezone to assume for naive datetimes

    Returns:
        Timezone-aware datetime object

    Raises:
        ValueError: If datetime cannot be parsed
    """
    try:
        # Try to parse as Unix timestamp first
        timestamp = float(dt)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (ValueError, TypeError):
        pass

    try:
        parsed = dateutil_parser.parse(dt)
    except Exception as e:
        raise ValueError(f"Cannot parse datetime: {dt}") from e

    # Make timezone-aware if naive
    if parsed.tzinfo is None:
        if assume_tz:
            parsed = parsed.replace(tzinfo=ZoneInfo(assume_tz))
        else:
            parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed
```

### src/mcp_server/tools/__init__.py

```python
"""Tool implementations for the MCP server."""

from mcp_server.tools.time_tools import convert_timezone, to_unix_time

__all__ = ["convert_timezone", "to_unix_time"]
```

### src/mcp_server/tools/time_tools.py

```python
"""Time and timezone related tools."""

from __future__ import annotations

from typing import Annotated, Literal, Optional

from zoneinfo import ZoneInfo

from mcp_server.utils import parse_datetime


def convert_timezone(
    dt: Annotated[str, "Datetime to convert (ISO 8601 or commonly parseable)"],
    from_tz: Annotated[str, "IANA time zone of the input (e.g., 'Europe/Madrid')"],
    to_tz: Annotated[str, "Target IANA time zone (e.g., 'America/New_York')"],
    out_format: Annotated[
        Optional[str],
        "Optional Python strftime format (default ISO 8601)",
    ] = None,
) -> str:
    """
    Convert a datetime from one IANA time zone to another.
    
    Returns ISO 8601 by default, or a custom strftime if provided.
    
    Examples:
        >>> convert_timezone("2025-08-10 09:30", "Europe/Madrid", "America/New_York")
        '2025-08-10T03:30:00-04:00'
        
        >>> convert_timezone("2025-08-10T09:30:00", "Europe/Madrid", "UTC", "%Y-%m-%d %H:%M")
        '2025-08-10 07:30'
    """
    # Parse with explicit input tz assumption for naive values
    aware_dt = parse_datetime(dt, assume_tz=from_tz)
    
    # Convert to target timezone
    converted = aware_dt.astimezone(ZoneInfo(to_tz))
    
    # Format output
    return converted.isoformat() if not out_format else converted.strftime(out_format)


def to_unix_time(
    dt: Annotated[str, "Datetime to convert (ISO 8601, common formats, or Unix int/float)"],
    tz: Annotated[
        Optional[str],
        "If dt is naive (no tz info), assume this IANA time zone (default UTC)",
    ] = None,
    unit: Annotated[
        Literal["seconds", "milliseconds"],
        "Output unit (default 'seconds')",
    ] = "seconds",
) -> float:
    """
    Convert a timestamp string into Unix time.
    
    - Accepts flexible date/time strings (via python-dateutil) or numeric Unix timestamps
    - If numeric, it is returned (optionally scaled to ms)
    
    Examples:
        >>> to_unix_time("2025-08-10T09:30:00+02:00", unit="seconds")
        1754892600.0
        
        >>> to_unix_time("1754892600", unit="milliseconds")
        1754892600000.0
    """
    # If dt is already a numeric timestamp, pass it through
    try:
        num = float(dt)
        return num if unit == "seconds" else num * 1000.0
    except ValueError:
        pass
    
    aware_dt = parse_datetime(dt, assume_tz=tz)
    unix_seconds = aware_dt.timestamp()
    
    return unix_seconds if unit == "seconds" else unix_seconds * 1000.0
```

### src/mcp_server/tools/file_tools.py

```python
"""File manipulation tools (example template)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional


def read_file(
    path: Annotated[str, "Path to the file to read"],
    encoding: Annotated[Optional[str], "File encoding (default: utf-8)"] = "utf-8",
) -> str:
    """
    Read contents of a file.
    
    Args:
        path: Path to the file
        encoding: Text encoding
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file cannot be read
    """
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    return file_path.read_text(encoding=encoding)


def write_file(
    path: Annotated[str, "Path to write the file"],
    content: Annotated[str, "Content to write"],
    encoding: Annotated[Optional[str], "File encoding (default: utf-8)"] = "utf-8",
    create_dirs: Annotated[bool, "Create parent directories if needed"] = True,
) -> str:
    """
    Write content to a file.
    
    Args:
        path: Path to the file
        content: Content to write
        encoding: Text encoding
        create_dirs: Whether to create parent directories
        
    Returns:
        Success message with file path
    """
    file_path = Path(path)
    
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_path.write_text(content, encoding=encoding)
    
    return f"Successfully wrote {len(content)} characters to {file_path.absolute()}"


def list_directory(
    path: Annotated[str, "Directory path to list"],
    pattern: Annotated[Optional[str], "Glob pattern to filter files (e.g., '*.txt')"] = None,
    recursive: Annotated[bool, "List recursively"] = False,
) -> list[str]:
    """
    List files in a directory.
    
    Args:
        path: Directory path
        pattern: Optional glob pattern
        recursive: Whether to list recursively
        
    Returns:
        List of file paths
        
    Raises:
        NotADirectoryError: If path is not a directory
    """
    dir_path = Path(path)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    if pattern:
        glob_method = dir_path.rglob if recursive else dir_path.glob
        files = glob_method(pattern)
    else:
        glob_method = dir_path.rglob if recursive else dir_path.glob
        files = glob_method("*")
    
    return [str(f) for f in files if f.is_file()]
```

### src/mcp_server/tools/data_tools.py

```python
"""Data processing tools (example template)."""

from __future__ import annotations

import json
from typing import Annotated, Any, Literal


def parse_json(
    text: Annotated[str, "JSON string to parse"],
    strict: Annotated[bool, "Use strict parsing mode"] = True,
) -> dict[str, Any]:
    """
    Parse a JSON string into a Python dictionary.
    
    Args:
        text: JSON string
        strict: Whether to use strict parsing
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    return json.loads(text, strict=strict)


def format_json(
    data: Annotated[dict[str, Any], "Data to format as JSON"],
    indent: Annotated[Optional[int], "Indentation level (None for compact)"] = 2,
    sort_keys: Annotated[bool, "Sort dictionary keys"] = False,
) -> str:
    """
    Format a Python object as JSON string.
    
    Args:
        data: Data to serialize
        indent: Indentation for pretty printing
        sort_keys: Whether to sort keys
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)


def filter_data(
    data: Annotated[list[dict[str, Any]], "List of dictionaries to filter"],
    field: Annotated[str, "Field name to filter by"],
    value: Annotated[Any, "Value to match"],
    operation: Annotated[
        Literal["equals", "contains", "greater", "less"],
        "Comparison operation"
    ] = "equals",
) -> list[dict[str, Any]]:
    """
    Filter a list of dictionaries by field value.
    
    Args:
        data: List of dictionaries
        field: Field to filter by
        value: Value to compare
        operation: Type of comparison
        
    Returns:
        Filtered list of dictionaries
    """
    result = []
    
    for item in data:
        if field not in item:
            continue
            
        item_value = item[field]
        
        if operation == "equals" and item_value == value:
            result.append(item)
        elif operation == "contains" and value in str(item_value):
            result.append(item)
        elif operation == "greater" and item_value > value:
            result.append(item)
        elif operation == "less" and item_value < value:
            result.append(item)
    
    return result
```

### src/mcp_server/server.py

```python
"""Main MCP server implementation using FastMCP."""

from __future__ import annotations

import structlog

from mcp.server.fastmcp import FastMCP

from mcp_server.core import configure_logging, get_config

# Import all tools
from mcp_server.tools import (
    convert_timezone,
    to_unix_time,
)

# Optional: Import additional tools as you create them
# from mcp_server.tools.file_tools import read_file, write_file, list_directory
# from mcp_server.tools.data_tools import parse_json, format_json, filter_data

logger = structlog.get_logger(__name__)

# Create the FastMCP instance
mcp = FastMCP("MCP Server Template")


def register_tools() -> None:
    """Register all tools with the MCP server."""
    
    # Register time tools
    mcp.tool()(convert_timezone)
    mcp.tool()(to_unix_time)
    
    # Register file tools (when ready)
    # mcp.tool()(read_file)
    # mcp.tool()(write_file)
    # mcp.tool()(list_directory)
    
    # Register data tools (when ready)
    # mcp.tool()(parse_json)
    # mcp.tool()(format_json)
    # mcp.tool()(filter_data)
    
    logger.info(f"Registered {len(mcp._tools)} tools: {list(mcp._tools.keys())}")


def main() -> None:
    """Main entry point for the server."""
    config = get_config()
    configure_logging(config.log_level)
    
    logger.info("Starting MCP server...")
    logger.info(f"Configuration: {config.model_dump()}")
    
    # Register all tools
    register_tools()
    
    # Run server with HTTP transport
    mcp.run(
        transport="http",
        host=config.host,
        port=config.port,
        path=config.path,
    )


if __name__ == "__main__":
    main()
```

### tests/conftest.py

```python
"""Pytest fixtures and configuration."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Generator

import pytest
from mcp.server.fastmcp import FastMCP

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mcp_server.server import mcp, register_tools


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mcp_server() -> FastMCP:
    """Get MCP server instance with registered tools for testing."""
    # Register tools if not already registered
    if not mcp._tools:
        register_tools()
    return mcp


@pytest.fixture
def sample_datetimes() -> dict[str, Any]:
    """Sample datetime test data."""
    return {
        "iso_with_tz": "2025-08-10T09:30:00+02:00",
        "iso_naive": "2025-08-10T09:30:00",
        "simple_format": "2025-08-10 09:30",
        "unix_timestamp": 1754899800,
        "timezones": {
            "madrid": "Europe/Madrid",
            "new_york": "America/New_York",
            "tokyo": "Asia/Tokyo",
            "utc": "UTC",
        },
    }


@pytest.fixture
def sample_files(tmp_path: Path) -> dict[str, Path]:
    """Create sample files for testing."""
    files = {}
    
    # Create test text file
    text_file = tmp_path / "test.txt"
    text_file.write_text("Hello, World!")
    files["text"] = text_file
    
    # Create test JSON file
    json_file = tmp_path / "data.json"
    json_file.write_text('{"name": "test", "value": 42}')
    files["json"] = json_file
    
    # Create subdirectory with files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file1.txt").write_text("File 1")
    (subdir / "file2.txt").write_text("File 2")
    files["subdir"] = subdir
    
    return files
```

### tests/test_server.py

```python
"""Tests for MCP server functionality."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.server import mcp, register_tools


def count_decorated_tools_in_source() -> int:
    """Count @mcp.tool decorated functions in server.py."""
    server_file = Path(__file__).parent.parent / "src" / "mcp_server" / "server.py"
    text = server_file.read_text(encoding="utf-8")
    
    # Count mcp.tool() registrations
    pattern = re.compile(r"mcp\.tool\(\)\([a-zA-Z_]+\)")
    return len(pattern.findall(text))


class TestServerStructure:
    """Test server structure and compliance."""
    
    def test_server_instance(self) -> None:
        """Test server instance is created."""
        assert isinstance(mcp, FastMCP)
        assert mcp.name == "MCP Server Template"
    
    def test_tool_registration(self, mcp_server: FastMCP) -> None:
        """Test tools are properly registered."""
        # Check that expected tools are registered
        tool_names = {tool.name for tool in mcp_server._tools.values()}
        expected_tools = {"convert_timezone", "to_unix_time"}
        
        assert expected_tools.issubset(tool_names)
    
    def test_tool_metadata(self, mcp_server: FastMCP) -> None:
        """Test tool metadata is complete."""
        for tool in mcp_server._tools.values():
            # Check name exists
            assert tool.name
            assert isinstance(tool.name, str)
            
            # Check description exists
            assert tool.description
            assert isinstance(tool.description, str)
            
            # Check input schema exists
            assert tool.input_schema
            assert isinstance(tool.input_schema, dict)
            assert tool.input_schema.get("type") == "object"
            assert "properties" in tool.input_schema
    
    def test_all_tools_registered(self) -> None:
        """Test that all defined tools are registered."""
        # Get all tool functions from tools package
        from mcp_server.tools import time_tools
        
        # Count functions that should be tools
        time_tool_funcs = [
            name for name in dir(time_tools)
            if not name.startswith("_") and callable(getattr(time_tools, name))
        ]
        
        # Ensure key functions are registered
        register_tools()  # Make sure tools are registered
        registered_names = {tool.name for tool in mcp._tools.values()}
        
        for func_name in ["convert_timezone", "to_unix_time"]:
            assert func_name in registered_names, f"Tool {func_name} not registered"
```

### tests/test_tools/__init__.py

```python
"""Tool-specific tests."""
```

### tests/test_tools/test_time_tools.py

```python
"""Tests for time tools."""

from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp_server.tools.time_tools import convert_timezone, to_unix_time
from mcp_server.utils import parse_datetime


class TestTimezoneConversion:
    """Test timezone conversion tool."""
    
    def test_basic_conversion(self, sample_datetimes: dict) -> None:
        """Test basic timezone conversion."""
        result = convert_timezone(
            dt="2025-08-10 09:30",
            from_tz="Europe/Madrid",
            to_tz="America/New_York",
        )
        
        assert "T03:30" in result or " 03:30" in result
        assert "-04:00" in result  # EDT offset
    
    def test_with_custom_format(self) -> None:
        """Test conversion with custom output format."""
        result = convert_timezone(
            dt="2025-08-10T09:30:00",
            from_tz="Europe/Madrid",
            to_tz="UTC",
            out_format="%Y-%m-%d %H:%M",
        )
        
        assert result == "2025-08-10 07:30"
    
    def test_naive_datetime_handling(self) -> None:
        """Test handling of naive datetimes."""
        result = convert_timezone(
            dt="2025-01-01 12:00",
            from_tz="UTC",
            to_tz="Europe/Madrid",
        )
        
        # Madrid is UTC+1 in January
        assert "13:00" in result
    
    def test_iso_format_with_timezone(self) -> None:
        """Test ISO format with timezone info."""
        result = convert_timezone(
            dt="2025-08-10T09:30:00Z",
            from_tz="UTC",
            to_tz="Europe/Madrid",
        )
        
        assert "+02:00" in result  # CEST offset


class TestUnixTime:
    """Test Unix time conversion tool."""
    
    def test_seconds_conversion(self) -> None:
        """Test conversion to Unix seconds."""
        result = to_unix_time(
            dt="2025-08-10T09:30:00+02:00",
            unit="seconds",
        )
        
        assert isinstance(result, float)
        assert result > 0
    
    def test_milliseconds_conversion(self) -> None:
        """Test conversion to Unix milliseconds."""
        result_sec = to_unix_time(
            dt="2025-08-10T09:30:00+02:00",
            unit="seconds",
        )
        result_ms = to_unix_time(
            dt="2025-08-10T09:30:00+02:00",
            unit="milliseconds",
        )
        
        assert abs(result_ms - (result_sec * 1000)) < 2
    
    def test_numeric_passthrough(self) -> None:
        """Test numeric timestamp passthrough."""
        timestamp = 1754899800
        result = to_unix_time(str(timestamp), unit="seconds")
        
        assert result == timestamp
    
    def test_naive_with_timezone(self) -> None:
        """Test naive datetime with specified timezone."""
        result_utc = to_unix_time("2025-01-01 00:00:00")
        result_madrid = to_unix_time(
            "2025-01-01 00:00:00",
            tz="Europe/Madrid",
        )
        
        # Madrid is UTC+1, so should be 1 hour earlier
        assert abs(result_utc - result_madrid) >= 3600 - 10
    
    def test_milliseconds_passthrough(self) -> None:
        """Test millisecond timestamp passthrough."""
        timestamp_ms = 1754899800000
        result = to_unix_time(str(timestamp_ms), unit="milliseconds")
        
        # Should recognize it's already in ms and pass through
        assert result == timestamp_ms


class TestDatetimeParser:
    """Test datetime parsing utility."""
    
    def test_parse_iso_format(self) -> None:
        """Test parsing ISO format."""
        dt = parse_datetime("2025-08-10T09:30:00Z")
        assert dt.year == 2025
        assert dt.month == 8
        assert dt.day == 10
        assert dt.hour == 9
        assert dt.minute == 30
    
    def test_parse_unix_timestamp(self) -> None:
        """Test parsing Unix timestamp."""
        dt = parse_datetime("1754899800")
        assert isinstance(dt, datetime)
        assert dt.tzinfo is not None
    
    def test_parse_with_timezone_assumption(self) -> None:
        """Test parsing with timezone assumption."""
        dt = parse_datetime("2025-01-01 12:00", assume_tz="Europe/Madrid")
        assert dt.tzinfo is not None
        assert dt.tzinfo == ZoneInfo("Europe/Madrid")
    
    def test_parse_various_formats(self) -> None:
        """Test parsing various datetime formats."""
        formats = [
            "2025-08-10",
            "2025/08/10",
            "10/08/2025",
            "Aug 10, 2025",
            "2025-08-10 09:30:00",
            "2025-08-10T09:30:00",
        ]
        
        for fmt in formats:
            dt = parse_datetime(fmt)
            assert isinstance(dt, datetime)
            assert dt.tzinfo is not None
```

### README.md

```markdown
# MCP Server Template

A reusable Python template for building Model Context Protocol (MCP) servers using FastMCP with HTTP transport.

## Features

- 🚀 **FastMCP Integration**: Built on FastMCP for automatic schema generation
- 🔧 **Type Safety**: Full Pydantic models and Python 3.13 typing
- 🧪 **Comprehensive Testing**: Pytest suite with async support
- 📦 **UV Package Management**: Modern Python dependency management
- 🔍 **Best Practices**: Follows Python and MCP standards
- 🎯 **Production Ready**: Logging, configuration, error handling
- 📁 **Modular Tools**: Organized tool structure for scalability

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager

### Installation

1. Clone this template:
```bash
git clone <your-repo-url>
cd mcp-server-template
```

2. Install dependencies with UV:
```bash
uv venv
uv pip install -e .
uv pip install -e ".[dev]"  # For development
```

3. Copy environment configuration:
```bash
cp .env.example .env
```

### Running the Server

```bash
# Using the script
python scripts/run_server.py

# Or directly
python -m mcp_server.server

# Or via entry point
mcp-server
```

The server will start on `http://127.0.0.1:8000/mcp/`

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test module
pytest tests/test_tools/test_time_tools.py

# Run specific test class
pytest tests/test_tools/test_time_tools.py::TestTimezoneConversion
```

### Using with LangChain/LangGraph

```bash
# Install agent dependencies
uv pip install -e ".[agent]"

# Run example agent
python examples/agent_client.py
```

## Development

### Adding New Tools

1. **Create a new tool module** in `src/mcp_server/tools/`:
```python
# src/mcp_server/tools/my_tools.py
from typing import Annotated

def my_new_tool(
    param: Annotated[str, "Parameter description"],
) -> str:
    """Tool description."""
    # Implementation
    return result
```

2. **Register the tool** in `src/mcp_server/server.py`:
```python
from mcp_server.tools.my_tools import my_new_tool

def register_tools() -> None:
    # ... existing registrations
    mcp.tool()(my_new_tool)
```

3. **Add tests** in `tests/test_tools/test_my_tools.py`

### Tool Organization

The template includes example tool categories:

- **`time_tools.py`**: Time and timezone operations
- **`file_tools.py`**: File system operations (template)
- **`data_tools.py`**: Data processing utilities (template)

Create new tool modules as needed:
- `api_tools.py`: External API integrations
- `db_tools.py`: Database operations
- `ml_tools.py`: Machine learning utilities
- `text_tools.py`: Text processing

### Type Checking

```bash
mypy src/
```

### Linting and Formatting

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/
```

## Project Structure

```
├── src/mcp_server/        # Main package
│   ├── server.py          # Server setup and tool registration
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration
│   ├── utils.py           # Shared utilities
│   └── tools/             # Tool implementations
│       ├── time_tools.py  # Time-related tools
│       ├── file_tools.py  # File operations
│       └── data_tools.py  # Data processing
├── tests/                 # Test suite
│   └── test_tools/        # Tool-specific tests
└── examples/              # Usage examples
```

## Configuration

Configure via environment variables or `.env` file:

- `MCP_HOST`: Server host (default: 127.0.0.1)
- `MCP_PORT`: Server port (default: 8000)
- `MCP_PATH`: MCP endpoint path (default: /mcp)
- `MCP_DEBUG`: Enable debug mode (default: false)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)

## Architecture

### Separation of Concerns

- **Tools** (`tools/`): Pure function implementations
- **Server** (`server.py`): Tool registration and MCP setup
- **Models** (`models.py`): Type definitions and validation
- **Config** (`config.py`): Environment and settings
- **Utils** (`utils.py`): Shared helper functions

### Tool Registration Pattern

```python
# 1. Define tool in tools/category.py
def my_tool(param: Annotated[str, "desc"]) -> str:
    """Tool implementation"""
    return result

# 2. Register in server.py
mcp.tool()(my_tool)
```

This pattern provides:
- Clear separation between implementation and registration
- Easy testing of tool functions
- Scalable organization for many tools
- Type safety and schema generation

## Testing Strategy

- **Unit Tests**: Test individual tool functions
- **Integration Tests**: Test MCP server setup
- **Type Tests**: Validate Pydantic models
- **Coverage**: Maintain >80% code coverage

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your tools in the appropriate category
4. Write comprehensive tests
5. Run tests and type checking
6. Submit a pull request
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
.mypy_cache/
.ruff_cache/

# Project specific
*.log
.env.local
.env.*.local
```

### .env.example

```env
# MCP Server Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
MCP_DEBUG=false
MCP_LOG_LEVEL=INFO

# OpenAI API Key (for agent examples)
OPENAI_API_KEY=sk-...
```