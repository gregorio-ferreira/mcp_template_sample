"""Simple FastMCP client example.

Short script demonstrating basic tool calls against the running MCP server.
Structured so it can be imported and exercised in tests.
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

SERVER_URL = "http://127.0.0.1:8000/mcp/"


async def run_example(base_url: str = SERVER_URL) -> dict[str, Any]:
    """Run the example interactions and return collected results.

    Returns a dict so tests can assert deterministically.
    """
    outputs: dict[str, Any] = {}
    async with Client(base_url) as client:
        await client.ping()
        print("Server is reachable!")
        outputs["ping"] = True

        tz_res = await client.call_tool(
            "convert_timezone",
            {
                "dt": "2025-08-10T09:30:00",
                "from_tz": "Europe/Madrid",
                "to_tz": "America/New_York",
            },
        )
        print("Convert Europe/Madrid -> America/New_York:", tz_res.data)
        outputs["convert_timezone"] = tz_res.data

        unix_res = await client.call_tool(
            "to_unix_time",
            {
                "dt": "2025-08-10T09:30:00+02:00",
                "unit": "milliseconds",
            },
        )
        print("Unix time (ms):", unix_res.data)
        outputs["to_unix_time"] = unix_res.data

    return outputs


async def main() -> None:  # pragma: no cover - thin wrapper
    await run_example()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
