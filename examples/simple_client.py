#!/usr/bin/env -S uv run python
"""Simple MCP Client Example.

This example demonstrates how to connect to an MCP server and use its tools.
It uses the FastMCP Python client to interact with the server.
"""

from __future__ import annotations

import asyncio

from fastmcp import Client

from mcp_server.core import get_server_url

# Server configuration
SERVER_URL = get_server_url()


async def main() -> None:
    """Simple example of using MCP tools."""
    print("🔗 Connecting to MCP server...")
    print(f"📍 Server URL: {SERVER_URL}")

    try:
        async with Client(SERVER_URL) as client:
            # Test server connectivity
            await client.ping()
            print("✅ Server connection successful")

            # Discover available tools
            tools = await client.list_tools()
            print(f"\n🔧 Available tools ({len(tools)}):")
            for tool in tools:
                print(f"   • {tool.name}: {tool.description}")

            # Example 1: Convert timezone
            print("\n🌍 Example 1: Timezone conversion")
            result = await client.call_tool(
                "convert_timezone",
                {
                    "dt": "2025-08-11 15:30",
                    "from_tz": "Europe/Madrid",
                    "to_tz": "America/New_York",
                },
            )
            print(f"   Madrid 15:30 → NYC: {result}")

            # Example 2: Unix timestamp
            print("\n⏰ Example 2: Unix timestamp")
            result = await client.call_tool(
                "to_unix_time",
                {
                    "dt": "2025-01-01T00:00:00Z",
                    "unit": "seconds",
                },
            )
            print(f"   2025-01-01 00:00:00 UTC → {result} seconds")

            print("\n🎉 All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure the MCP server is running:")
        print("   uv run python scripts/run_server.py")


if __name__ == "__main__":
    asyncio.run(main())
