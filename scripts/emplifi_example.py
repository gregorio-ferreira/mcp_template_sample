#!/usr/bin/env python3
"""
Example script demonstrating Emplifi Listening API tools.

This script shows how to use the Emplifi integration to:
1. List listening queries
2. Fetch recent posts
3. Get metrics

Usage:
  # Set up your environment variables first (using Basic Auth)
  export EMPLIFI_TOKEN="your_token"
  export EMPLIFI_SECRET="your_secret"
  
  # OR using OAuth (requires interactive login)
  export EMPLIFI_CLIENT_ID="your_client_id"
  export EMPLIFI_CLIENT_SECRET="your_client_secret"
  export EMPLIFI_REDIRECT_URI="http://localhost:8765/callback"
  
  # Then run the example
  python scripts/emplifi_example.py
"""

import asyncio
import json
import os
from datetime import datetime, timedelta

from mcp_server.core.config import load_environment
from mcp_server.tools.emplifi_tools import (
    DimensionConfig,
    MetricConfig,
    fetch_listening_metrics,
    get_daily_mention_metrics,
    get_recent_posts,
    list_listening_queries,
)


async def main():
    """Main example function."""
    print("🎯 Emplifi Listening API Example")
    print("=" * 40)
    
    try:
        # 1. List all listening queries
        print("\n📋 Listing all listening queries...")
        queries = await list_listening_queries()
        
        if not queries:
            print("❌ No listening queries found. Check your authentication.")
            return
        
        print(f"✅ Found {len(queries)} listening queries:")
        for query in queries[:5]:  # Show first 5
            print(f"   • {query.id}: {query.name}")
            if query.description:
                print(f"     Description: {query.description}")
        
        if len(queries) > 5:
            print(f"   ... and {len(queries) - 5} more")
        
        # Use the first query for examples
        first_query = queries[0]
        query_id = first_query.id
        print(f"\n🔍 Using query '{first_query.name}' ({query_id}) for examples...")
        
        # 2. Get recent posts
        print(f"\n📰 Fetching recent posts for the last 7 days...")
        recent_posts = await get_recent_posts(
            query_id=query_id,
            days_back=7,
            limit_per_page=10,
            max_pages=1
        )
        
        print(f"✅ Found {len(recent_posts)} recent posts:")
        for post in recent_posts[:3]:  # Show first 3
            created_time = post.created_time[:19] if post.created_time else "Unknown"
            message_preview = post.message[:100] + "..." if len(post.message) > 100 else post.message
            print(f"   • [{post.platform}] {created_time}")
            print(f"     Author: {post.author.get('name', 'Unknown')}")
            print(f"     Message: {message_preview}")
            if post.sentiment:
                print(f"     Sentiment: {post.sentiment}")
            print()
        
        if len(recent_posts) > 3:
            print(f"   ... and {len(recent_posts) - 3} more posts")
        
        # 3. Get daily mention metrics
        print(f"\n📊 Fetching daily mention metrics for the last 30 days...")
        metrics = await get_daily_mention_metrics(
            query_id=query_id,
            days_back=30
        )
        
        print(f"✅ Retrieved metrics with {len(metrics.data)} data points:")
        total_mentions = sum(
            day_data.get("mentions", 0) 
            for day_data in metrics.data 
            if isinstance(day_data, dict)
        )
        print(f"   📈 Total mentions in last 30 days: {total_mentions}")
        
        # Show last 5 days
        if metrics.data:
            print("   📅 Last 5 days:")
            for day_data in metrics.data[-5:]:
                if isinstance(day_data, dict):
                    date = day_data.get("date", "Unknown")
                    mentions = day_data.get("mentions", 0)
                    print(f"     {date}: {mentions} mentions")
        
        # 4. Advanced metrics example
        print(f"\n🔍 Fetching custom metrics...")
        try:
            custom_metrics = await fetch_listening_metrics(
                query_ids=[query_id],
                date_start=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                date_end=datetime.now().strftime("%Y-%m-%d"),
                metrics=[MetricConfig(type="mentions")],
                dimensions=[DimensionConfig(type="date.day")]
            )
            
            print(f"✅ Custom metrics retrieved: {len(custom_metrics.data)} data points")
            if custom_metrics.meta:
                print(f"   Metadata: {json.dumps(custom_metrics.meta, indent=2)}")
        
        except Exception as e:
            print(f"⚠️  Could not fetch custom metrics: {e}")
        
        print(f"\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tips:")
        print("   • Check that your environment variables are set correctly")
        print("   • Ensure you have valid Emplifi API credentials")
        print("   • For OAuth, make sure you've completed the initial authentication")
        print("   • Check that you have access to listening queries in your account")


if __name__ == "__main__":
    # Load environment variables from .env file
    load_environment()
    
    # Check environment
    required_vars = ["EMPLIFI_CLIENT_ID", "EMPLIFI_CLIENT_SECRET", "EMPLIFI_REDIRECT_URI"]
    basic_vars = ["EMPLIFI_TOKEN", "EMPLIFI_SECRET"]
    
    has_oauth = all(os.environ.get(var) for var in required_vars)
    has_basic = all(os.environ.get(var) for var in basic_vars)
    
    if not (has_oauth or has_basic):
        print("❌ Missing required environment variables!")
        print("\nFor OAuth authentication, set:")
        for var in required_vars:
            print(f"   export {var}='your_value'")
        print("\nOR for Basic authentication, set:")
        for var in basic_vars:
            print(f"   export {var}='your_value'")
        exit(1)
    
    if has_oauth:
        print("🔐 Using OAuth authentication")
    else:
        print("🔐 Using Basic authentication")
    
    asyncio.run(main())
