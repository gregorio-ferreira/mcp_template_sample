#!/usr/bin/env python3
"""
Integration test example for Emplifi API with Syngenta Flowers query.

This script demonstrates how to use the Emplifi tools to retrieve
all data for the "Syngenta Flowers" listening query for the year 2025.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.tools.emplifi_tools import (  # noqa: E402
    MetricConfig,
    fetch_listening_metrics,
    fetch_listening_posts,
    get_daily_mention_metrics,
    get_recent_posts,
    list_listening_queries,
)

# Test constants
TEST_QUERY_ID = "LNQ_1140092_641afbbd98a766f5eb4a4915"
TEST_QUERY_NAME = "Syngenta Flowers"
YEAR_2025_START = "2025-01-01"
YEAR_2025_END = "2025-12-31"


async def verify_query_exists() -> bool:
    """Verify that the Syngenta Flowers query exists in the account."""
    print("🔍 Checking if Syngenta Flowers query exists...")

    try:
        queries = await list_listening_queries()
        print(f"📊 Found {len(queries)} total listening queries")

        # Look for our specific query
        target_query = None
        for query in queries:
            if query.id == TEST_QUERY_ID:
                target_query = query
                break

        if target_query:
            print("✅ Found target query:")
            print(f"   ID: {target_query.id}")
            print(f"   Name: {target_query.name}")
            print(f"   Description: {target_query.description}")
            print(f"   Status: {target_query.status}")
            return True
        else:
            print("❌ Target query not found in account")
            print("Available queries:")
            for query in queries[:5]:  # Show first 5
                print(f"   - {query.name} ({query.id})")
            if len(queries) > 5:
                print(f"   ... and {len(queries) - 5} more")
            return False

    except Exception as e:
        print(f"❌ Error checking queries: {e}")
        return False


async def test_fetch_posts_year_2025() -> None:
    """Test fetching posts for Syngenta Flowers for the year 2025."""
    print("\n📝 Testing post fetching for 2025...")

    try:
        posts = await fetch_listening_posts(
            query_ids=[TEST_QUERY_ID],
            date_start=YEAR_2025_START,
            date_end=YEAR_2025_END,
            limit=50,  # Get up to 50 posts per page
            max_pages=3  # Limit to 3 pages for testing
        )

        print(f"📄 Retrieved {len(posts)} posts for 2025")

        if posts:
            print("📊 Post breakdown by platform:")
            platforms = {}
            sentiments = {}

            for post in posts:
                # Count by platform
                platform = post.platform
                platforms[platform] = platforms.get(platform, 0) + 1

                # Count by sentiment if available
                if hasattr(post, 'sentiment') and post.sentiment:
                    sentiment = post.sentiment
                    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

            for platform, count in platforms.items():
                print(f"   {platform}: {count} posts")

            if sentiments:
                print("💭 Sentiment breakdown:")
                for sentiment, count in sentiments.items():
                    print(f"   {sentiment}: {count} posts")

            # Show some example posts
            print("\n📝 Example posts:")
            for i, post in enumerate(posts[:3]):  # Show first 3
                print(f"\n   Post {i+1}:")
                print(f"     Platform: {post.platform}")
                print(f"     Created: {post.created_time}")
                print(f"     Author: {post.author.get('name', 'Unknown')}")
                print(f"     Message: {post.message[:100]}...")
                if hasattr(post, 'sentiment') and post.sentiment:
                    print(f"     Sentiment: {post.sentiment}")
        else:
            print("📭 No posts found for 2025")

    except Exception as e:
        print(f"❌ Error fetching posts: {e}")


async def test_fetch_metrics_year_2025() -> None:
    """Test fetching metrics for Syngenta Flowers for the year 2025."""
    print("\n📈 Testing metrics fetching for 2025...")

    try:
        # Test different metric types
        metric_types = ["mentions", "reach", "engagement"]

        for metric_type in metric_types:
            print(f"\n📊 Fetching {metric_type} metrics...")

            try:
                metrics = await fetch_listening_metrics(
                    query_ids=[TEST_QUERY_ID],
                    date_start=YEAR_2025_START,
                    date_end=YEAR_2025_END,
                    metrics=[MetricConfig(type=metric_type)]
                )

                print(f"📈 Retrieved {len(metrics.data)} data points")

                if metrics.meta:
                    print(f"📋 Meta information: {metrics.meta}")

                if metrics.data:
                    # Calculate some basic statistics
                    values = []
                    for data_point in metrics.data:
                        if metric_type in data_point:
                            values.append(data_point[metric_type])

                    if values:
                        total = sum(values)
                        avg = total / len(values)
                        max_val = max(values)
                        min_val = min(values)

                        print(f"   Total {metric_type}: {total}")
                        print(f"   Average daily {metric_type}: {avg:.2f}")
                        print(f"   Max daily {metric_type}: {max_val}")
                        print(f"   Min daily {metric_type}: {min_val}")
                    else:
                        print(f"   No {metric_type} data available")
                else:
                    print(f"   No {metric_type} data points found")

            except Exception as metric_error:
                print(f"⚠️  Error fetching {metric_type}: {metric_error}")

    except Exception as e:
        print(f"❌ Error in metrics testing: {e}")


async def test_convenience_functions() -> None:
    """Test the convenience functions."""
    print("\n🛠️  Testing convenience functions...")

    try:
        # Test recent posts (last 30 days)
        print("\n📅 Getting recent posts (last 30 days)...")
        recent_posts = await get_recent_posts(
            TEST_QUERY_ID,
            days_back=30,
            max_pages=2
        )
        print(f"📄 Found {len(recent_posts)} recent posts")

        # Test daily mention metrics (last 90 days)
        print("\n📊 Getting daily mention metrics (last 90 days)...")
        daily_metrics = await get_daily_mention_metrics(
            TEST_QUERY_ID,
            days_back=90
        )
        print(f"📈 Retrieved {len(daily_metrics.data)} daily data points")

        if daily_metrics.data:
            # Find the most active day
            max_mentions = 0
            max_date = None
            total_mentions = 0

            for data_point in daily_metrics.data:
                if "mentions" in data_point:
                    mentions = data_point["mentions"]
                    total_mentions += mentions
                    if mentions > max_mentions:
                        max_mentions = mentions
                        max_date = data_point.get("date", "Unknown")

            print(f"   Total mentions in last 90 days: {total_mentions}")
            if max_date:
                print(f"   Most active day: {max_date} with {max_mentions} mentions")

    except Exception as e:
        print(f"❌ Error testing convenience functions: {e}")


async def main() -> None:
    """Main test function."""
    print("🚀 Starting Emplifi Integration Test for Syngenta Flowers")
    print("=" * 60)

    # First verify the query exists
    query_exists = await verify_query_exists()
    if not query_exists:
        print("\n❌ Cannot proceed without the target query. Exiting.")
        return

    # Run all tests
    await test_fetch_posts_year_2025()
    await test_fetch_metrics_year_2025()
    await test_convenience_functions()

    print("\n" + "=" * 60)
    print("🎉 Integration test completed!")
    print("\nNote: This test demonstrates the Emplifi API integration.")
    print("The amount of data returned depends on the actual activity")
    print("for the Syngenta Flowers query in your Emplifi account.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
