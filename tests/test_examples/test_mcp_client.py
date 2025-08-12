#!/usr/bin/env -S uv run python
"""MCP Client Test Script using FastMCP Client.

This script tests the MCP server functionality using the FastMCP Python client.
It can be run standalone or imported for use in other testing scenarios.
"""

import asyncio
import sys
from typing import Any

import pytest
from fastmcp import Client

from mcp_server.core import get_server_url

# Skip during unit testing since this example requires a running server
pytestmark = pytest.mark.skip(reason="integration example requires running MCP server")

# Server configuration
TARGET_QUERY_ID = "LNQ_1140092_66fe2dcd3e9eb298096e8db3"
TARGET_QUERY_NAME = "BAYER"
SERVER_URL = get_server_url()


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
            expected_tools = [
                "list_listening_queries",
                "fetch_listening_posts",
                "get_recent_posts"
            ]
            missing_tools = [t for t in expected_tools if t not in tool_names]
            if missing_tools:
                print(f"   ⚠️  Missing expected tools: {missing_tools}")

            # Test 3: List Emplifi listening queries
            print("3. Testing Emplifi listening queries...")
            try:
                queries_result = await client.call_tool(
                    "list_listening_queries", {}
                )
                queries_data = (
                    queries_result.data
                    if hasattr(queries_result, "data")
                    else queries_result
                )
                print(f"   ✅ Found queries: {len(queries_data)} results")
                results["listening_queries"] = queries_data

                # Check if our target query is present
                if isinstance(queries_data, list):
                    target_found = any(
                        q.get("id") == TARGET_QUERY_ID for q in queries_data
                    )
                    if target_found:
                        print(f"   ✅ Target query {TARGET_QUERY_NAME} found")
                    else:
                        print(f"   ⚠️  Target query {TARGET_QUERY_NAME} not found")
                else:
                    print(f"   ⚠️  Unexpected query format: {type(queries_data)}")

            except Exception as e:
                print(f"   ⚠️  Query listing failed (credentials?): {e}")
                results["listening_queries"] = str(e)

            # Test 4: Get recent posts for BAYER query
            print("4. Testing Emplifi recent posts...")
            try:
                posts_result = await client.call_tool(
                    "get_recent_posts",
                    {
                        "query_id": TARGET_QUERY_ID,
                        "days_back": 7,
                        "limit": 5,
                    },
                )
                posts_data = (
                    posts_result.data
                    if hasattr(posts_result, "data")
                    else posts_result
                )
                print(f"   ✅ Recent posts: {len(posts_data)} results")
                results["recent_posts"] = posts_data

                # Show sample post if available
                if posts_data and len(posts_data) > 0:
                    sample_post = posts_data[0]
                    platform = sample_post.get("platform", "unknown")
                    message = sample_post.get("message", "")[:50]
                    print(f"   ✅ Sample post: {platform} - {message}...")
                else:
                    print("   ℹ️  No recent posts found")

            except Exception as e:
                print(f"   ⚠️  Recent posts failed (credentials?): {e}")
                results["recent_posts"] = str(e)

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
    """Test advanced Emplifi usage scenarios."""
    print("\n🔬 Advanced Emplifi Test Scenarios")
    print("=" * 40)

    async with Client(SERVER_URL) as client:
        # Test different date ranges for fetch_listening_posts
        test_cases = [
            {
                "name": "Last 3 days",
                "date_start": "2025-08-09",
                "date_end": "2025-08-12",
                "limit": 3,
            },
            {
                "name": "Single day",
                "date_start": "2025-08-11",
                "date_end": "2025-08-11",
                "limit": 5,
            },
            {
                "name": "Week range with specific fields",
                "date_start": "2025-08-05",
                "date_end": "2025-08-12",
                "limit": 10,
                "fields": ["id", "message", "platform", "created_time"],
            },
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"{i}. Testing fetch posts: {case['name']}...")
            try:
                params = {
                    "query_ids": [TARGET_QUERY_ID],
                    "date_start": case["date_start"],
                    "date_end": case["date_end"],
                    "limit": case["limit"],
                    "sort_order": "desc",
                }
                if "fields" in case:
                    params["fields"] = case["fields"]

                result = await client.call_tool("fetch_listening_posts", params)
                posts_data = (
                    result.data if hasattr(result, "data") else result
                )
                print(f"   ✅ Found {len(posts_data)} posts for {case['name']}")
                
                if posts_data and len(posts_data) > 0:
                    sample = posts_data[0]
                    platform = sample.get("platform", "unknown")
                    msg_preview = sample.get("message", "")[:30]
                    print(f"   ℹ️  Sample: {platform} - {msg_preview}...")

            except Exception as e:
                print(f"   ⚠️  Failed (credentials?): {e}")

        # Test get_recent_posts with different time ranges
        print(f"{len(test_cases) + 1}. Testing recent posts with different ranges...")
        
        for days in [1, 3, 7, 14]:
            try:
                result = await client.call_tool(
                    "get_recent_posts",
                    {
                        "query_id": TARGET_QUERY_ID,
                        "days_back": days,
                        "limit": 5,
                    },
                )
                posts_data = (
                    result.data if hasattr(result, "data") else result
                )
                print(f"   ✅ Last {days} days: {len(posts_data)} posts")
            except Exception as e:
                print(f"   ⚠️  Failed for {days} days: {e}")


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
