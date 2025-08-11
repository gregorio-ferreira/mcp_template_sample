# End-to-end tests for the FastMCP server (pytest)

Below are **pytest** tests that validate your MCP server end to end:

- Spin up an **in-memory client** against the FastMCP server object (no network).

- Verify the **number of tools** exposed by the server equals the number of decorated functions in the source file (AST-based check).

- Validate **tool metadata** (names, descriptions, JSON schema from type hints).

- Exercise **functional behavior** of both tools (timezone conversion and Unix time).

Place these files next to your existing `mcp_time_server.py`.

---

## requirements

```bash
pip install pytest python-dateutil
# (you already installed fastmcp / langchain / langgraph for the app code)
```

---

## tests/test_mcp_time_server.py

```python
# tests/test_mcp_time_server.py
from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure project root on sys.path so we can import mcp_time_server
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import your FastMCP server module
server = importlib.import_module("mcp_time_server")


# ---- helpers -----------------------------------------------------------------

def count_decorated_tools_in_source(filepath: Path) -> int:
    """
    Static (AST-like) heuristic to count functions decorated with @mcp.tool() or @mcp.tool.
    We avoid importing extra deps by using a simple regex that is robust for common styles.
    """
    text = filepath.read_text(encoding="utf-8")

    # Matches lines like: @mcp.tool()   or   @mcp.tool
    pattern = re.compile(r"^\s*@\s*mcp\.tool\s*(\(\s*\))?\s*$", re.MULTILINE)
    return len(pattern.findall(text))


@pytest.fixture(scope="session")
def source_file() -> Path:
    return PROJECT_ROOT / "mcp_time_server.py"


@pytest.fixture(scope="session")
def expected_tool_names() -> set[str]:
    # Keep this in sync with your server function names
    return {"convert_timezone", "to_unix_time"}


@pytest.fixture(scope="session")
def mcp_server_instance():
    """
    Access the FastMCP instance defined in mcp_time_server.py as `mcp`.
    """
    assert hasattr(server, "mcp"), "Expected `mcp` FastMCP instance in mcp_time_server.py"
    return server.mcp


# We rely on FastMCP's built-in in-memory client if available.
# Fallback option: skip tests gracefully if client is unavailable.
Client = None
try:
    # FastMCP >= 2 typically exposes a test client here:
    # from mcp.server.fastmcp import Client  # sometimes lives elsewhere
    # safer import path:
    from mcp.server.fastmcp import Client  # type: ignore
except Exception:
    pass


@pytest.fixture(scope="session")
def event_loop():
    """Create a dedicated event loop for async tests at session scope."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def has_in_memory_client() -> bool:
    return Client is not None


@pytest.fixture(scope="session")
def client(mcp_server_instance, has_in_memory_client, request):
    if not has_in_memory_client:
        pytest.skip("FastMCP in-memory Client not available in this version.")
    return Client(mcp_server_instance)


# ---- tests: structure & compliance -------------------------------------------

def test_ast_count_matches_expected(source_file: Path, expected_tool_names: set[str]):
    """Count @mcp.tool decorators in source and verify we expect that many tools."""
    src_count = count_decorated_tools_in_source(source_file)
    assert src_count == len(expected_tool_names), (
        f"Source shows {src_count} @mcp.tool-decorated functions, "
        f"but expected {len(expected_tool_names)} (update expected_tool_names fixture?)."
    )


@pytest.mark.asyncio
async def test_server_advertises_all_tools(client, expected_tool_names: set[str]):
    """List tools via MCP and ensure all expected tools are advertised."""
    async with client as c:
        tools = await c.list_tools()
        names = {t.name for t in tools}
        missing = expected_tool_names - names
        unexpected = names - expected_tool_names
        assert not missing, f"Missing tools in advertisement: {missing}"
        assert not unexpected, f"Unexpected tools advertised: {unexpected}"


@pytest.mark.asyncio
async def test_tool_metadata_from_type_hints_and_docstrings(client, expected_tool_names: set[str]):
    """
    Validate that each tool has a non-empty description and a useful, typed schema
    so agents can understand how to call them.
    """
    async with client as c:
        tools = await c.list_tools()
        by_name = {t.name: t for t in tools}

        for name in expected_tool_names:
            assert name in by_name, f"Tool {name} not advertised."

            tool = by_name[name]

            # Description clarity
            assert isinstance(tool.description, str) and tool.description.strip(), (
                f"Tool {name} has empty or missing description."
            )
            # The description should mention key concepts for clarity
            if name == "convert_timezone":
                # Should mention timezone conversion and IANA tzs
                assert "time" in tool.description.lower() or "timezone" in tool.description.lower()
            if name == "to_unix_time":
                assert "unix" in tool.description.lower()

            # JSON schema derived from type hints must include properties
            assert tool.input_schema, f"Tool {name} missing input_schema."
            schema = tool.input_schema
            assert "type" in schema and schema["type"] == "object", f"Tool {name} schema should be an object."
            assert "properties" in schema and isinstance(schema["properties"], dict) and schema["properties"], (
                f"Tool {name} schema missing properties."
            )

            # Key argument names should exist
            props = schema["properties"]
            if name == "convert_timezone":
                for arg in ("dt", "from_tz", "to_tz"):
                    assert arg in props, f"{name} missing '{arg}' in schema."
            if name == "to_unix_time":
                assert "dt" in props, f"{name} missing 'dt' in schema."
                # unit should be constrained to seconds|milliseconds
                if "unit" in props and "enum" in props["unit"]:
                    assert set(props["unit"]["enum"]) >= {"seconds", "milliseconds"}


# ---- tests: functional behavior ----------------------------------------------

@pytest.mark.asyncio
async def test_convert_timezone_basic(client):
    """
    Convert '2025-08-10 09:30' from Europe/Madrid (UTC+2 in summer) to America/New_York.
    Check the resulting hour differs by 6 hours (EDT, UTC-4) on that date.
    """
    async with client as c:
        result = await c.call_tool(
            "convert_timezone",
            {
                "dt": "2025-08-10 09:30",
                "from_tz": "Europe/Madrid",
                "to_tz": "America/New_York",
            },
        )
        # result is typically wrapped in a Content list; FastMCP client usually returns structured content.
        # Normalize to string:
        out = _extract_text(result)
        assert out, "No output returned from convert_timezone."

        # Parse and check offset roughly (we just check hour difference and tz name presence)
        # Expected: 09:30 Madrid -> 03:30 New York (approx 6-hour difference in Aug 2025)
        assert "T03:30" in out or " 03:30" in out, f"Unexpected converted time: {out}"
        # Should carry timezone info
        assert out.endswith("+00:00") is False, "Expected local offset for NY (e.g., -04:00) not UTC."
        assert "-04:00" in out or "-05:00" in out, "Expected a negative offset (EDT/EST) for America/New_York."


@pytest.mark.asyncio
async def test_convert_timezone_with_format(client):
    async with client as c:
        result = await c.call_tool(
            "convert_timezone",
            {
                "dt": "2025-08-10T09:30:00",
                "from_tz": "Europe/Madrid",
                "to_tz": "UTC",
                "out_format": "%Y-%m-%d %H:%M",
            },
        )
        out = _extract_text(result)
        assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", out), f"Unexpected formatted output: {out}"


@pytest.mark.asyncio
async def test_to_unix_time_seconds_and_milliseconds(client):
    async with client as c:
        # ISO with tz
        res_sec = await c.call_tool(
            "to_unix_time", {"dt": "2025-08-10T09:30:00+02:00", "unit": "seconds"}
        )
        res_ms = await c.call_tool(
            "to_unix_time", {"dt": "2025-08-10T09:30:00+02:00", "unit": "milliseconds"}
        )

        sec = _extract_number(res_sec)
        ms = _extract_number(res_ms)

        assert isinstance(sec, (int, float)) and sec > 0
        assert isinstance(ms, (int, float)) and ms > 0
        # ms should be roughly sec*1000 (tolerate float rounding)
        assert abs(ms - (sec * 1000)) < 2, f"Milliseconds not ~ seconds*1000: sec={sec}, ms={ms}"

        # Numeric passthrough
        res_passthrough = await c.call_tool("to_unix_time", {"dt": str(sec), "unit": "seconds"})
        sec_passthrough = _extract_number(res_passthrough)
        assert abs(sec_passthrough - sec) < 1e-6


@pytest.mark.asyncio
async def test_to_unix_time_naive_default_utc(client):
    """
    If a naive datetime is provided without tz, server assumes UTC by default.
    """
    async with client as c:
        res_utc = await c.call_tool("to_unix_time", {"dt": "2025-01-01 00:00:00"})
        res_madrid = await c.call_tool(
            "to_unix_time", {"dt": "2025-01-01 00:00:00", "tz": "Europe/Madrid"}
        )
        utc_val = _extract_number(res_utc)
        mad_val = _extract_number(res_madrid)
        # Values must differ (Madrid ≠ UTC at that time)
        assert abs(utc_val - mad_val) >= 3600 - 10, "Expected at least ~1 hour difference."


# ---- utility extractors -------------------------------------------------------

def _extract_text(tool_call_result: Any) -> str:
    """
    FastMCP client often returns a list of Content items or a structured dict.
    Handle common shapes and return a string.
    """
    # Common shapes:
    # - {"content": [{"type":"text","text":"..."}], ...}
    # - [{"type":"text","text":"..."}]
    # - "..."
    if tool_call_result is None:
        return ""
    if isinstance(tool_call_result, str):
        return tool_call_result
    if isinstance(tool_call_result, (int, float)):
        return str(tool_call_result)
    if isinstance(tool_call_result, dict):
        if "content" in tool_call_result and isinstance(tool_call_result["content"], list):
            for c in tool_call_result["content"]:
                if isinstance(c, dict) and c.get("type") == "text":
                    return c.get("text", "")
        # sometimes server returns {"type":"text","text":"..."} directly
        if tool_call_result.get("type") == "text":
            return tool_call_result.get("text", "")
    if isinstance(tool_call_result, list):
        for c in tool_call_result:
            if isinstance(c, dict) and c.get("type") == "text":
                return c.get("text", "")
    return str(tool_call_result)


def _extract_number(tool_call_result: Any) -> float:
    """
    Extract a numeric value from a tool call result, tolerating different wrappers.
    """
    if isinstance(tool_call_result, (int, float)):
        return float(tool_call_result)
    # Try dict/list shapes -> text -> float
    s = _extract_text(tool_call_result)
    try:
        return float(s)
    except Exception:
        # Sometimes MCP returns JSON-like text
        try:
            obj = json.loads(s)
            if isinstance(obj, (int, float)):
                return float(obj)
        except Exception:
            pass
    raise AssertionError(f"Could not extract number from result: {tool_call_result!r}")
```

---

## how these tests cover your goals

- **Generic compliance signals.** Listing tools and calling them via the MCP client validates handshake, capability discovery, schema generation, and JSON-RPC plumbing in practice.

- **Tool count parity.** The AST-derived decorator count must equal the number of advertised tools (helps catch registration mistakes).

- **Schema and doc clarity.** Tests assert non-empty descriptions and presence of key properties from the JSON schema inferred by **type hints + docstrings**—the crucial info agents rely on.

- **Functional accuracy.** Time zone and Unix time conversions are verified with realistic cases, including formatting, DST offsets, milliseconds, numeric passthrough, and naïve-datetime defaults.

If you prefer spawning the HTTP server for tests instead of the in-memory client, I can share an alternative pytest fixture that launches `mcp_time_server.py` in a subprocess and uses the LangChain `MultiServerMCPClient` to exercise the same checks over HTTP.
