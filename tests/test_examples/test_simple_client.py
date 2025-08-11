"""Tests for the simple_client example."""
from __future__ import annotations

import threading
import time
from typing import Any

import httpx
import pytest

from mcp_server.server import mcp, register_tools
from examples.simple_client import run_example, SERVER_URL


@pytest.fixture(scope="module", autouse=True)  # type: ignore[misc]
def _start_server() -> None:
    """Start the MCP server in a background thread for example tests.

    Uses the FastMCP http transport (stateless) at default URL.
    """
    register_tools()

    def _run() -> None:
        # Run stateless HTTP server
        mcp.run(
            transport="http",
            host="127.0.0.1",
            port=8000,
            path="/mcp",
            stateless_http=True,
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    # Wait briefly for server to start
    time.sleep(0.5)


@pytest.mark.asyncio  # type: ignore[misc]
async def test_simple_client_tools() -> None:
    results = await run_example(SERVER_URL)
    assert results["ping"] is True
    converted = str(results["convert_timezone"])
    assert (
        "America/New_York" in converted
        or "-04" in converted
        or "T03:30" in converted
    )
    # Coerce to float to ensure numeric without tuple isinstance pattern
    _ = float(results["to_unix_time"])  # no exception means numeric


@pytest.mark.asyncio  # type: ignore[misc]
async def test_raw_http_call() -> None:
    """Call the convert_timezone tool via raw HTTP JSON-RPC request."""
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "convert_timezone",
        "params": {
            "dt": "2025-08-10T09:30:00",
            "from_tz": "Europe/Madrid",
            "to_tz": "UTC",
        },
    }
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(SERVER_URL, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("result") is not None
    # Basic expected hour check (09:30 Madrid summer -> 07:30 UTC)
    assert "07:30" in str(data["result"]).replace("T", " ")
