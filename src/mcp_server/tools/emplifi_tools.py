"""Emplifi Listening API tools for MCP server.

This module provides simplified tools for interacting with the Emplifi API
using Basic Authentication. Supports listing queries and fetching posts.
"""

from __future__ import annotations

import asyncio
import base64
import inspect
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
import structlog
from pydantic import BaseModel, Field, HttpUrl

from mcp_server.core.config import (
    get_emplifi_credentials,
    get_emplifi_settings,
)

logger = structlog.get_logger(__name__)

API_BASE, DEFAULT_TIMEOUT = get_emplifi_settings()


# Models
class ListeningQuery(BaseModel):
    """A listening query from the Emplifi API."""

    id: str
    name: str
    description: str | None = None
    status: str | None = None


class ListeningAuthor(BaseModel):
    """Author information for a listening post."""

    id: str | None = None
    name: str | None = None
    username: str | None = None
    url: HttpUrl | None = None


class ListeningPost(BaseModel):
    """A listening post (mention) from the Emplifi API."""

    id: str
    created_time: datetime = Field(..., alias="created_time")
    platform: str
    author: ListeningAuthor | None = None
    message: str
    sentiment: str | None = None
    interactions: int | None = None
    url: HttpUrl | None = None


# Authentication helper
def _get_auth_headers() -> dict[str, str]:
    """Build Basic authentication headers from configured credentials."""
    token, secret = get_emplifi_credentials()

    if not token or not secret:
        msg = (
            "Missing Emplifi credentials. Set EMPLIFI_TOKEN and "
            "EMPLIFI_SECRET environment variables."
        )
        logger.error(msg)
        raise ValueError(msg)

    # Encode token:secret as base64
    credentials = f"{token}:{secret}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")

    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


# Internal HTTP helper with exponential backoff for transient errors
async def _send_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json: dict[str, Any] | None = None,
    max_retries: int = 3,
    backoff_base: float = 0.05,
) -> httpx.Response:
    """Send an HTTP request with basic retry on 429 and 5xx responses.

    Returns the first successful (2xx/3xx) or non‑retryable (4xx except 429)
    response, or the last response after exhausting retries.
    """
    last: httpx.Response | None = None
    delay = backoff_base
    for attempt in range(1, max_retries + 1):
        verb = method.lower()
        call = getattr(client, verb, None)
        try:
            if callable(call):  # use patched get/post in tests
                result = call(
                    url,
                    headers=headers,
                    json=json,
                    timeout=DEFAULT_TIMEOUT,
                )
                if inspect.isawaitable(result):
                    last = await result
                else:  # synchronous mock result
                    last = result
            else:  # pragma: no cover
                last = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    timeout=DEFAULT_TIMEOUT,
                )
        except httpx.RequestError as exc:  # network issue -> always retry
            logger.warning(
                "HTTP request error, will retry if attempts remain",
                error=str(exc),
                attempt=attempt,
                max_retries=max_retries,
            )
            if attempt == max_retries:
                raise
            await asyncio.sleep(delay)
            delay *= 2
            continue

        raw_status = getattr(last, "status_code", 200)
        try:  # normalise status for mocks
            status_int = int(raw_status)
        except (TypeError, ValueError):  # pragma: no cover
            status_int = 200

        # Success or non‑retryable client error (other than 429)
        if 200 <= status_int < 400 or (
            400 <= status_int < 500 and status_int != 429
        ):
            return last

        # Retryable (429 or 5xx)
        if attempt == max_retries:
            return last
        await asyncio.sleep(delay)
        delay *= 2

    assert last is not None  # for type narrowing
    return last

# Core API functions


async def _list_listening_queries_raw(
    headers: dict[str, str]
) -> list[dict[str, Any]]:
    """GET /3/listening/queries and return raw list of query dicts."""
    url = f"{API_BASE}/listening/queries"

    async with httpx.AsyncClient() as client:
        response = await _send_with_retries(
            client, "GET", url, headers=headers
        )
        rfs = response.raise_for_status()
        # httpx's raise_for_status is sync, but tests may patch it with an
        # AsyncMock; support both to avoid RuntimeWarnings.
        if inspect.isawaitable(rfs):  # pragma: no branch
            await rfs  # pragma: no cover - depends on test mocks
        else:  # pragma: no branch
            rfs()
        body = response.json()

    # Handle different response structures
    data = body.get("data")
    if isinstance(data, list):
        return data

    if isinstance(body, list):
        return body

    if "queries" in body and isinstance(body["queries"], list):
        return body["queries"]

    # Fallback: wrap body in a list
    return [body]


async def _fetch_all_posts_raw(
    headers: dict[str, str],
    date_start: str,
    date_end: str,
    listening_queries: list[str],
    fields: list[str] | None = None,
    sort_field: str | None = None,
    sort_order: str = "desc",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """POST /3/listening/posts and follow cursor pagination."""
    url = f"{API_BASE}/listening/posts"

    payload: dict[str, Any] = {
        "date_start": date_start,
        "date_end": date_end,
        "listening_queries": listening_queries,
        "limit": min(limit, 100),  # API max is 100
    }

    if fields:
        payload["fields"] = fields
    if sort_field:
        payload["sort"] = [{"field": sort_field, "order": sort_order}]

    all_posts: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        # First page
        response = await _send_with_retries(
            client, "POST", url, headers=headers, json=payload
        )
        rfs = response.raise_for_status()
        if inspect.isawaitable(rfs):
            await rfs  # pragma: no cover
        else:  # pragma: no branch
            rfs()
        body = response.json()

        data_block = body.get("data", {})
        posts = data_block.get("posts", [])
        all_posts.extend(posts)
        next_cursor = data_block.get("next")

        # Subsequent pages
        while next_cursor:
            response = await _send_with_retries(
                client,
                "POST",
                url,
                headers=headers,
                json={"next": next_cursor},
            )
            rfs = response.raise_for_status()
            if inspect.isawaitable(rfs):
                await rfs  # pragma: no cover
            else:  # pragma: no branch
                rfs()
            body = response.json()

            data_block = body.get("data", {})
            posts = data_block.get("posts", [])
            all_posts.extend(posts)
            next_cursor = data_block.get("next")

    return all_posts


# MCP Tool Functions
async def list_listening_queries() -> list[ListeningQuery]:
    """List all available listening queries from Emplifi.

    This tool connects to the Emplifi Listening API and retrieves all listening
    queries that are accessible to your account. Listening queries are the
    search configurations that monitor social media platforms for specific
    keywords, hashtags, mentions, or other criteria.

    Returns:
        A list of ListeningQuery objects containing:
        - id: Unique identifier for the query (used in fetch_listening_posts)
        - name: Human-readable name of the query
        - description: Optional description of what the query monitors
        - status: Current status of the query (active, paused, etc.)

    Authentication:
        Requires EMPLIFI_TOKEN and EMPLIFI_SECRET environment variables.
        Uses Basic Authentication with the Emplifi API.

    Example Usage:
        queries = await list_listening_queries()
        for query in queries:
            print(f"Query: {query.name} (ID: {query.id})")

    Common Use Cases:
        - Discover available monitoring queries for your account
        - Get query IDs needed for fetching posts
        - Check query status and descriptions
        - List all social listening configurations
    """
    headers = _get_auth_headers()
    queries_raw = await _list_listening_queries_raw(headers)

    return [
        ListeningQuery(
            id=query["id"],
            name=query.get("name", ""),
            description=query.get("description"),
            status=query.get("status"),
        )
        for query in queries_raw
    ]


async def fetch_listening_posts(
    query_ids: Annotated[list[str], "List of listening query IDs"],
    date_start: Annotated[str, "Start date (YYYY-MM-DD or ISO format)"],
    date_end: Annotated[str, "End date (YYYY-MM-DD or ISO format)"],
    fields: Annotated[list[str] | None, "Fields to include"] = None,
    sort_field: Annotated[str | None, "Field to sort by"] = "interactions",
    sort_order: Annotated[str, "Sort order (asc/desc)"] = "desc",
    limit: Annotated[int, "Posts per page (max 100)"] = 100,
) -> list[ListeningPost]:
    """Fetch listening posts for specified queries and date range.

    This tool retrieves social media posts, mentions, and conversations that
    match your listening queries within a specified time period. It auto-
    handles pagination to fetch all available posts across multiple API calls.

    Args:
    query_ids: List of listening query IDs (see list_listening_queries)
        date_start: Start date in YYYY-MM-DD format (e.g., "2025-08-01") or
                   ISO format (e.g., "2025-08-01T00:00:00Z")
        date_end: End date in same format as date_start
    fields: Optional list of fields to include. If None, includes:
               ["id", "created_time", "platform", "author", "message",
                "sentiment", "interactions", "url"]
        sort_field: Field to sort results by. Valid options: "interactions",
                   "comments", "potential_impressions", "shares"
                   (default: "interactions")
    sort_order: Sort direction - "asc" or "desc" (newest first default)
        limit: Number of posts per API page (max 100, API limitation)

    Returns:
        List of ListeningPost objects containing:
        - id: Unique post identifier
        - created_time: When the post was created (ISO format)
        - platform: Social media platform (twitter, facebook, instagram, etc.)
        - author: Dictionary with author information (name, handle, etc.)
        - message: Text content of the post
        - sentiment: Sentiment analysis result (positive, negative, neutral)
        - interactions: Number of likes, shares, comments, etc.
        - url: Direct link to the original post

    Authentication:
        Requires EMPLIFI_TOKEN and EMPLIFI_SECRET environment variables.

    Date Range:
        - Maximum range depends on your Emplifi plan (typically 30-90 days)
        - Use shorter ranges for better performance with high-volume queries
        - Dates are inclusive (includes posts from both start and end dates)

    Pagination:
        - Automatically fetches all pages of results
        - Each page contains up to 'limit' posts (max 100)
        - Large result sets may take longer to process

    Example Usage:
        # Get last week's posts for a specific query
        posts = await fetch_listening_posts(
            query_ids=["LNQ_1140092_66fe2dcd3e9eb298096e8db3"],
            date_start="2025-08-01",
            date_end="2025-08-07",
            sort_field="interactions",
            sort_order="desc",
            limit=50
        )

        # Get posts from multiple queries
        posts = await fetch_listening_posts(
            query_ids=["query1", "query2", "query3"],
            date_start="2025-08-01",
            date_end="2025-08-02"
        )

    Common Use Cases:
        - Monitor brand mentions across social platforms
        - Analyze sentiment trends over time
        - Extract high-engagement posts for content ideas
        - Track campaign performance and reach
        - Generate reports on social media coverage
        - Find influencer content and user-generated content
    """
    headers = _get_auth_headers()

    # Default fields if not specified
    if fields is None:
        fields = [
            "id",
            "created_time",
            "platform",
            "author",
            "message",
            "sentiment",
            "interactions",
            "url",
        ]

    # Convert dates to simple YYYY-MM-DD format for the API
    def format_date(date_str: str) -> str:
        if "T" in date_str:
            # ISO format, extract date part only
            return date_str.split("T")[0]
        return date_str  # Already in YYYY-MM-DD format

    posts_raw = await _fetch_all_posts_raw(
        headers=headers,
        date_start=format_date(date_start),
        date_end=format_date(date_end),
        listening_queries=query_ids,
        fields=fields,
        sort_field=sort_field,
        sort_order=sort_order,
        limit=limit,
    )

    # Convert to Pydantic models
    posts: list[ListeningPost] = []
    for post in posts_raw:
        try:
            posts.append(ListeningPost.model_validate(post, context=None))
        except (ValueError, TypeError) as e:
            post_id = post.get("id", "unknown")
            logger.warning(
                "Skipping malformed post", post_id=post_id, error=str(e)
            )
            continue

    return posts


async def get_recent_posts(
    query_id: Annotated[str, "Listening query ID"],
    days_back: Annotated[int, "Number of days back to fetch"] = 7,
    limit: Annotated[int, "Posts per page"] = 50,
) -> list[ListeningPost]:
    """Get recent posts for a specific listening query.

    This is a convenience tool for recent posts from the last N days for a
    single listening query. Good for quick checks or dashboards.

    Args:
        query_id: Listening query ID (get from list_listening_queries)
        days_back: Number of days to look back from today (default: 7)
        limit: Maximum posts per page to fetch (default: 50, max: 100)

    Returns:
        List of recent ListeningPost objects, sorted by interactions
        (highest engagement first)

    Date Calculation:
        - End date: Today (current date in UTC)
        - Start date: Today minus 'days_back' days
        - Times are automatically set to cover the full date range

    Authentication:
        Requires EMPLIFI_TOKEN and EMPLIFI_SECRET environment variables.

    Example Usage:
        # Get last week's posts for a query
        recent_posts = await get_recent_posts(
            query_id="LNQ_1140092_66fe2dcd3e9eb298096e8db3",
            days_back=7,
            limit=25
        )

        # Get yesterday's posts
        yesterday_posts = await get_recent_posts(
            query_id="your_query_id",
            days_back=1,
            limit=100
        )

    Common Use Cases:
        - Daily monitoring dashboards
        - Quick sentiment checks
        - Recent activity summaries
        - Real-time social media tracking
        - Automated daily reports
        - Testing query configurations
    """
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days_back)

    return await fetch_listening_posts(
        query_ids=[query_id],
        date_start=start_date.strftime("%Y-%m-%d"),
        date_end=end_date.strftime("%Y-%m-%d"),
        limit=limit,
        sort_field="interactions",
        sort_order="desc",
    )
