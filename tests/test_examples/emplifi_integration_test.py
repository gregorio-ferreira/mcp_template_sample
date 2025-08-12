#!/usr/bin/env python3
"""
Integration test example for Emplifi API with BAYER query.

This script demonstrates how to use the Emplifi tools to retrieve
all data for the "BAYER" listening query for recent periods.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.tools.emplifi_tools import (  # noqa: E402
    fetch_listening_posts,
    get_recent_posts,
    list_listening_queries,
)

# Test constants
TEST_QUERY_ID = "LNQ_1140092_66fe2dcd3e9eb298096e8db3"
TEST_QUERY_NAME = "BAYER"
TEST_DATE_START = "2025-08-05"
TEST_DATE_END = "2025-08-12"


async def verify_query_exists() -> bool:
    """Verify that the BAYER query exists in the account."""
    print("🔍 Checking if BAYER query exists...")

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


async def test_fetch_posts_recent() -> None:
    """Test fetching posts for BAYER for recent period."""
    print("\n📝 Testing post fetching for recent period...")

    try:
        posts = await fetch_listening_posts(
            query_ids=[TEST_QUERY_ID],
            date_start=TEST_DATE_START,
            date_end=TEST_DATE_END,
            limit=50,  # Get up to 50 posts per page
        )

        print(f"📄 Retrieved {len(posts)} posts for {TEST_DATE_START} to {TEST_DATE_END}")

        if posts:
            print("📊 Post breakdown by platform:")
            platforms = {}
            sentiments = {}

            for post in posts:
                # Count by platform
                platform = post.platform
                platforms[platform] = platforms.get(platform, 0) + 1

                # Count by sentiment if available
                if post.sentiment:
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
                author_name = "Unknown"
                if isinstance(post.author, dict):
                    author_name = post.author.get("name", "Unknown")
                print(f"     Author: {author_name}")
                print(f"     Message: {post.message[:100]}...")
                if post.sentiment:
                    print(f"     Sentiment: {post.sentiment}")
        else:
            print("📭 No posts found for the specified period")

    except Exception as e:
        print(f"❌ Error fetching posts: {e}")


async def test_get_recent_posts() -> None:
    """Test the get_recent_posts convenience function."""
    print("\n�️  Testing get_recent_posts convenience function...")

    try:
        # Test recent posts (last 7 days)
        print("\n� Getting recent posts (last 7 days)...")
        recent_posts = await get_recent_posts(
            TEST_QUERY_ID,
            days_back=7,
            limit=20
        )
        print(f"� Found {len(recent_posts)} recent posts")

        if recent_posts:
            # Show platform distribution
            platforms: dict[str, int] = {}
            for post in recent_posts:
                platform = post.platform
                platforms[platform] = platforms.get(platform, 0) + 1

            print("📊 Recent posts by platform:")
            for platform, count in platforms.items():
                print(f"   {platform}: {count} posts")

            # Show most recent post
            if recent_posts:
                latest_post = recent_posts[0]
                print("\n📝 Most recent post:")
                print(f"   Platform: {latest_post.platform}")
                print(f"   Created: {latest_post.created_time}")
                print(f"   Message: {latest_post.message[:80]}...")

    except Exception as e:
        print(f"❌ Error testing get_recent_posts: {e}")


async def test_different_date_ranges() -> None:
    """Test fetching posts with different date ranges."""
    print("\n📅 Testing different date ranges...")

    date_ranges = [
        ("2025-08-11", "2025-08-11", "Single day"),
        ("2025-08-10", "2025-08-12", "3-day range"),
        ("2025-08-05", "2025-08-12", "Week range"),
    ]

    for start_date, end_date, description in date_ranges:
        print(f"\n📊 Testing {description} ({start_date} to {end_date})...")
        try:
            posts = await fetch_listening_posts(
                query_ids=[TEST_QUERY_ID],
                date_start=start_date,
                date_end=end_date,
                limit=10,
            )
            print(f"   📄 Found {len(posts)} posts for {description}")

        except Exception as e:
            print(f"   ❌ Error for {description}: {e}")


async def main() -> None:
    """Main test function."""
    print("🚀 Starting Emplifi Integration Test for BAYER")
    print("=" * 60)

    # First verify the query exists
    query_exists = await verify_query_exists()
    if not query_exists:
        print("\n❌ Cannot proceed without the target query. Exiting.")
        return

    # Run all tests
    await test_fetch_posts_recent()
    await test_get_recent_posts()
    await test_different_date_ranges()

    print("\n" + "=" * 60)
    print("🎉 Integration test completed!")
    print("\nNote: This test demonstrates the Emplifi API integration.")
    print("The amount of data returned depends on the actual activity")
    print("for the BAYER query in your Emplifi account.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
