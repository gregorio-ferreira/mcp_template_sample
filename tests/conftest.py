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

from mcp_server.server import mcp, register_tools  # noqa: E402


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def mcp_server() -> FastMCP:
    """Return MCP server with registered tools."""
    register_tools()
    return mcp


@pytest.fixture
def sample_datetimes() -> dict[str, Any]:
    """Sample datetime test data."""
    return {
        "iso": "2025-08-10T09:30:00+02:00",
        "naive": "2025-08-10 09:30:00",
        "numeric": "1754899800",
    }
