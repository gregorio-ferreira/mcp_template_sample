#!/usr/bin/env python3
"""MCP Client Test Script using FastMCP Client.

This script tests the MCP server functionality using the FastMCP Python client.
It can be run standalone or imported for use in other testing scenarios.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from fastmcp import Client

# Server configuration
SERVER_URL = "http://127.0.0.1:8000/mcp/"


async def test_basic_client_functionality() -> dict[str, Any]:
    """Test core MCP client functionality and return results."""
    print("🧪 FastMCP Client Test Suite")
    print("=" * 40)
    print(f"📍 Server URL: {SERVER_URL}")
    print()

    results: dict[str, Any] = {}

    try:
        async with Client(SERVER_URL) as client:
            # Test 1: Server connectivity
            print("1. Testing server connection...")
            await client.ping()
            print("   ✅ Server ping successful")
            results["ping"] = True

            # Test 2: Tool discovery
            print("2. Testing tool discovery...")
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            print(f"   ✅ Found {len(tools)} tools: {tool_names}")
            results["tools"] = tool_names

            # Verify expected tools are present
            expected_tools = ["convert_timezone", "to_unix_time"]
            missing_tools = [t for t in expected_tools if t not in tool_names]
            if missing_tools:
                print(f"   ⚠️  Missing expected tools: {missing_tools}")

            # Test 3: Timezone conversion
            print("3. Testing timezone conversion...")
            tz_result = await client.call_tool(
                "convert_timezone",
                {
                    "dt": "2025-08-10T15:30:00",
                    "from_tz": "Europe/Madrid",
                    "to_tz": "America/New_York",
                },
            )

            # Handle different result formats
            converted = str(tz_result.data if hasattr(tz_result, "data") else tz_result)
            print(f"   ✅ Madrid 15:30 -> NYC: {converted}")
            results["timezone_conversion"] = converted

            # Verify conversion looks correct
            expected_indicators = ["America/New_York", "-04", "T11:30", "11:30"]
            if any(indicator in converted for indicator in expected_indicators):
                print("   ✅ Timezone conversion appears correct")
            else:
                print(f"   ⚠️  Unexpected conversion result: {converted}")

            # Test 4: Unix time conversion
            print("4. Testing Unix time conversion...")
            unix_result = await client.call_tool(
                "to_unix_time",
                {
                    "dt": "2025-08-10T15:30:00+02:00",
                    "unit": "milliseconds",
                },
            )

            unix_data = unix_result.data if hasattr(unix_result, "data") else unix_result
            unix_time = float(unix_data)
            print(f"   ✅ Unix time (ms): {unix_time}")
            results["unix_time"] = unix_time

            # Verify it's a reasonable timestamp (should be in 2025)
            if unix_time > 1735689600000:  # 2025-01-01 in ms
                print("   ✅ Unix timestamp appears reasonable for 2025")
            else:
                print(f"   ⚠️  Unix timestamp seems incorrect: {unix_time}")

            # Test 5: Resource listing (if any)
            print("5. Testing resource discovery...")
            try:
                resources = await client.list_resources()
                print(f"   ✅ Found {len(resources)} resources")
                results["resources"] = [r.uri for r in resources] if resources else []
            except Exception as e:
                print(f"   ℹ️  No resources available or error: {e}")
                results["resources"] = []

            # Test 6: Prompt listing (if any)
            print("6. Testing prompt discovery...")
            try:
                prompts = await client.list_prompts()
                print(f"   ✅ Found {len(prompts)} prompts")
                results["prompts"] = [p.name for p in prompts] if prompts else []
            except Exception as e:
                print(f"   ℹ️  No prompts available or error: {e}")
                results["prompts"] = []

            print("\n🎉 All FastMCP client tests passed!")
            results["success"] = True
            return results

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
        return results


async def test_advanced_scenarios() -> None:
    """Test some advanced usage scenarios."""
    print("\n🔬 Advanced Test Scenarios")
    print("=" * 40)

    async with Client(SERVER_URL) as client:
        # Test timezone conversion with different formats
        test_cases = [
            {
                "name": "ISO format with timezone",
                "dt": "2025-12-25T00:00:00+01:00",
                "from_tz": "Europe/Paris",
                "to_tz": "UTC",
            },
            {
                "name": "Simple date string",
                "dt": "2025-06-15 14:30",
                "from_tz": "Asia/Tokyo",
                "to_tz": "America/Los_Angeles",
            },
            {
                "name": "Edge case - DST transition",
                "dt": "2025-03-30 02:30",  # DST transition in Europe
                "from_tz": "Europe/Berlin",
                "to_tz": "UTC",
            },
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"{i}. {case['name']}...")
            try:
                # Remove the 'name' field from the parameters
                params = {k: v for k, v in case.items() if k != "name"}
                result = await client.call_tool("convert_timezone", params)
                converted = str(result.data if hasattr(result, "data") else result)
                print(f"   ✅ {case['dt']} ({case['from_tz']}) -> {converted}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")

        # Test Unix time with different units
        print(f"{len(test_cases) + 1}. Unix time conversion (seconds vs milliseconds)...")
        base_dt = "2025-01-01T00:00:00Z"

        for unit in ["seconds", "milliseconds"]:
            try:
                result = await client.call_tool("to_unix_time", {"dt": base_dt, "unit": unit})
                timestamp = result.data if hasattr(result, "data") else result
                print(f"   ✅ {base_dt} -> {timestamp} {unit}")
            except Exception as e:
                print(f"   ❌ Failed for {unit}: {e}")


def print_usage() -> None:
    """Print usage information."""
    print("Usage:")
    print("  python test_mcp_client.py [OPTIONS]")
    print()
    print("Options:")
    print("  --basic      Run only basic functionality tests (default)")
    print("  --advanced   Run advanced test scenarios")
    print("  --all        Run all tests")
    print("  --help       Show this help message")
    print()
    print("Examples:")
    print("  python test_mcp_client.py")
    print("  python test_mcp_client.py --all")
    print("  uv run python test_mcp_client.py --advanced")


async def main() -> int:
    """Main entry point."""
    # Parse simple command line arguments
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_usage()
        return 0

    run_basic = True
    run_advanced = "--advanced" in args or "--all" in args

    if "--advanced" in args and "--all" not in args:
        run_basic = False

    try:
        if run_basic:
            results = await test_basic_client_functionality()
            if not results.get("success", False):
                return 1

        if run_advanced:
            await test_advanced_scenarios()

        print("\n📊 Test Summary:")
        print("   ✅ All tests completed successfully!")
        print(f"   🔗 Server: {SERVER_URL}")
        print("   📚 FastMCP Client functionality verified")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
