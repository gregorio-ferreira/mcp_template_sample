# End-to-end MCP demo: FastMCP (HTTP) server + LangChain/LangGraph agent

Below you’ll find **two runnable Python programs**:

- `mcp_time_server.py` — an MCP server (FastMCP) exposing two tools:
  
  - `convert_timezone`: convert a datetime between IANA time zones.
  
  - `to_unix_time`: convert a timestamp into Unix time (seconds or milliseconds).

- `agent_mcp_client.py` — a LangGraph agent that discovers those tools via **`MultiServerMCPClient`** (HTTP transport) and uses them from chat.

> Notes
> 
> - The server uses **FastMCP** with the recommended HTTP/streamable-HTTP transport (simple `.run(transport="http", host, port, path)` entrypoint). ([GitHub](https://github.com/jlowin/fastmcp?utm_source=chatgpt.com "jlowin/fastmcp: 🚀 The fast, Pythonic way to build MCP ..."))
> 
> - The agent uses **LangChain MCP Adapters** and **LangGraph** with `MultiServerMCPClient` to auto-discover tools and wire them into a ReAct agent. ([GitHub](https://github.com/langchain-ai/langchain-mcp-adapters "GitHub - langchain-ai/langchain-mcp-adapters: LangChain  MCP"))

---

## quickstart

```bash
# 1) Create a fresh venv (recommended)
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install dependencies
pip install "fastmcp>=2.0" "langchain-mcp-adapters>=0.1.9" langgraph "langchain[openai]" python-dateutil

# 3) Start the MCP server (serves HTTP at http://127.0.0.1:8000/mcp/)
python mcp_time_server.py

# 4) In a second terminal, export your OpenAI key and run the agent
export OPENAI_API_KEY=sk-...   # or set via your preferred secrets manager
python agent_mcp_client.py
```

---

## mcp_time_server.py (FastMCP server, HTTP transport)

```python
# mcp_time_server.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional, Literal
from zoneinfo import ZoneInfo

from dateutil import parser as dateutil_parser
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TimeTools")


def _parse_datetime(dt: str, assume_tz: Optional[str] = None) -> datetime:
    """
    Parse a wide range of datetime strings into an aware datetime.
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


@mcp.tool()
def convert_timezone(
    dt: Annotated[str, "Datetime to convert (ISO 8601 or commonly parseable)."],
    from_tz: Annotated[str, "IANA time zone of the input (e.g., 'Europe/Madrid')."],
    to_tz: Annotated[str, "Target IANA time zone (e.g., 'America/New_York')."],
    out_format: Annotated[
        Optional[str],
        "Optional Python strftime format (default ISO 8601).",
    ] = None,
) -> str:
    """
    Convert a datetime from one IANA time zone to another.
    Returns ISO 8601 by default, or a custom strftime if provided.
    """
    # Parse with explicit input tz assumption for naïve values
    aware_dt = _parse_datetime(dt, assume_tz=from_tz)

    # Convert
    converted = aware_dt.astimezone(ZoneInfo(to_tz))

    return converted.isoformat() if not out_format else converted.strftime(out_format)


@mcp.tool()
def to_unix_time(
    dt: Annotated[str, "Datetime to convert (ISO 8601, common formats, or Unix int/float)."],
    tz: Annotated[
        Optional[str],
        "If `dt` is naïve (no tz info), assume this IANA time zone (default UTC).",
    ] = None,
    unit: Annotated[
        Literal["seconds", "milliseconds"],
        "Output unit (default 'seconds').",
    ] = "seconds",
) -> float:
    """
    Convert a timestamp string into Unix time.
    - Accepts flexible date/time strings (via python-dateutil) or numeric Unix timestamps.
    - If numeric, it is returned (optionally scaled to ms).
    """
    # If `dt` is already a numeric timestamp, pass it through
    try:
        num = float(dt)
        return num if unit == "seconds" else num * 1000.0
    except ValueError:
        pass

    aware_dt = _parse_datetime(dt, assume_tz=tz)
    unix_seconds = aware_dt.timestamp()
    return unix_seconds if unit == "seconds" else unix_seconds * 1000.0


if __name__ == "__main__":
    # Serve Streamable-HTTP on localhost:8000 at path /mcp
    # (FastMCP maps "http" to the Streamable HTTP transport.)
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
```

Why this shape?

- **FastMCP** auto-generates MCP tool schemas from **type hints + docstrings**, so the agent can discover arguments and descriptions without extra config.

- `transport="http"` is the recommended deployment style for web services; clients use `transport="streamable_http"` when connecting. ([GitHub](https://github.com/jlowin/fastmcp?utm_source=chatgpt.com "jlowin/fastmcp: 🚀 The fast, Pythonic way to build MCP ..."))

---

## agent_mcp_client.py (LangChain + LangGraph agent)

```python
# agent_mcp_client.py
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model


async def main():
    # 1) Connect to the MCP server via Streamable HTTP
    client = MultiServerMCPClient(
        {
            "time_tools": {
                "transport": "streamable_http",
                "url": "http://127.0.0.1:8000/mcp/",
                # If you add auth later:
                # "headers": {"Authorization": "Bearer <token>"},
            }
        }
    )

    # 2) Discover tools from the server (no manual tool wiring needed)
    tools = await client.get_tools()

    # 3) Create a simple ReAct-style agent with those tools
    # Use any chat model supported by LangChain (OpenAI shown here).
    model = init_chat_model("openai:gpt-4.1")
    agent = create_react_agent(model, tools)

    # 4) Try a couple of calls
    print("\n--- Example 1: timezone conversion ---")
    res1 = await agent.ainvoke(
        {
            "messages": (
                "Convert '2025-08-10 09:30' from Europe/Madrid to America/New_York. "
                "Return ISO 8601."
            )
        }
    )
    print(res1["messages"][-1].content)

    print("\n--- Example 2: unix time (ms) ---")
    res2 = await agent.ainvoke(
        {
            "messages": (
                "Convert '2025-08-10T09:30:00+02:00' to Unix time in milliseconds."
            )
        }
    )
    print(res2["messages"][-1].content)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

What’s happening?

- `MultiServerMCPClient` connects to your HTTP MCP server at `/mcp/`, **pulls the tools** and exposes them as LangChain tools; `create_react_agent` plugs them straight into an agent loop. ([GitHub](https://github.com/langchain-ai/langchain-mcp-adapters "GitHub - langchain-ai/langchain-mcp-adapters: LangChain  MCP"))

- You don’t need to hard-code tool names/args; MCP discovery handles that dynamically.

---

## testing tips

- **MCP Inspector**: run `npx @modelcontextprotocol/inspector` and point it to `http://127.0.0.1:8000/mcp/` to manually exercise the tools and verify schemas/results. ([Model Context Protocol](https://modelcontextprotocol.io/docs/tools/inspector?utm_source=chatgpt.com "Inspector"), [GitHub](https://github.com/modelcontextprotocol/inspector?utm_source=chatgpt.com "modelcontextprotocol/inspector: Visual testing tool for MCP ..."), [Cloudflare Docs](https://developers.cloudflare.com/agents/guides/test-remote-mcp-server/?utm_source=chatgpt.com "Test a Remote MCP Server"))

- **LangGraph StateGraph**: if you’d like a more explicit tool loop, the adapters also show a `StateGraph` wiring with `ToolNode` and `tools_condition`. ([GitHub](https://github.com/langchain-ai/langchain-mcp-adapters "GitHub - langchain-ai/langchain-mcp-adapters: LangChain  MCP"))

---

## requirements.txt (optional)

```text
fastmcp>=2.0
langchain-mcp-adapters>=0.1.9
langgraph
langchain[openai]
python-dateutil
```

---

## common gotchas

- **Naïve datetimes**: the server assumes UTC unless you pass `from_tz`/`tz`.

- **IANA names**: use canonical names (e.g., `Europe/Madrid`, `America/New_York`) for reliability.

- **HTTP path**: client URL must include the trailing `/mcp/` path used by the server. ([GitHub](https://github.com/langchain-ai/langchain-mcp-adapters "GitHub - langchain-ai/langchain-mcp-adapters: LangChain  MCP"))

If you want, I can extend this with unit tests (pytest) that call the tools via an MCP client and assert conversions edge-to-edge.
