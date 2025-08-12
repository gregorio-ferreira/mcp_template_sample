"""Emplifi Listening API tools for MCP server.

This module provides tools for interacting with the Emplifi Listening API,
including OAuth2 authentication, listing queries, fetching posts, and
retrieving metrics.
"""

from __future__ import annotations

import base64
import contextlib
import json
import os
import threading
import time
import webbrowser
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Annotated, Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import structlog
from pydantic import BaseModel

from mcp_server.core.config import load_environment

logger = structlog.get_logger(__name__)

# Constants
API_BASE = "https://api.emplifi.io"
OAUTH_BASE = f"{API_BASE}/oauth2/0"
TOKEN_FILE = "emplifi_token.json"


# Models
class EmplifiConfig(BaseModel):
    """Configuration for Emplifi API authentication."""
    client_id: str | None = None
    client_secret: str | None = None
    redirect_uri: str | None = None
    scopes: str = "api.read offline_access"
    basic_token: str | None = None
    basic_secret: str | None = None


class ListeningQuery(BaseModel):
    """A listening query from the Emplifi API."""
    id: str
    name: str
    description: str | None = None
    status: str | None = None


class ListeningPost(BaseModel):
    """A listening post (mention) from the Emplifi API."""
    id: str
    created_time: str
    platform: str
    author: dict[str, Any]
    message: str
    sentiment: str | None = None
    interactions: int | None = None
    url: str | None = None


class ListeningMetrics(BaseModel):
    """Metrics response from the Emplifi API."""
    # API returns different types based on dimensions
    data: list[dict[str, Any] | int | float | str]
    meta: dict[str, Any] | None = None


class PostsFilter(BaseModel):
    """Filter for posts requests."""
    field: str
    value: Any


class PostsSort(BaseModel):
    """Sort configuration for posts."""
    field: str
    order: str = "desc"


class MetricConfig(BaseModel):
    """Metric configuration."""
    metric: str


class DimensionConfig(BaseModel):
    """Dimension configuration."""
    type: str
    group: dict[str, Any] | None = None


# Authentication Classes
class TokenStorage:
    """Handle token storage and retrieval."""

    @staticmethod
    def save_token(token: dict[str, Any]) -> None:
        """Save token to file."""
        try:
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(token, f, indent=2)
        except Exception as e:
            logger.error("Failed to save token", error=str(e))

    @staticmethod
    def load_token() -> dict[str, Any]:
        """Load token from file."""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Failed to load token", error=str(e))
        return {}


class EmplifiAuthClient:
    """Base authentication client."""

    def __init__(self, config: EmplifiConfig):
        self.config = config

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        raise NotImplementedError


class EmplifiOAuthClient(EmplifiAuthClient):
    """OAuth2 authentication client for Emplifi API."""

    def __init__(self, config: EmplifiConfig):
        super().__init__(config)
        self.token = TokenStorage.load_token()
        self.auth_endpoint = f"{OAUTH_BASE}/auth"
        self.token_endpoint = f"{OAUTH_BASE}/token"

    def _have_valid_access_token(self) -> bool:
        """Check if we have a valid access token."""
        if not self.token or "access_token" not in self.token:
            return False
        obtained_at = self.token.get("obtained_at", 0)
        expires_in = self.token.get("expires_in", 0)
        exp = obtained_at + expires_in - 60
        return time.time() < exp

    def _basic_client_auth_header(self) -> str:
        """Generate basic auth header for client credentials."""
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        encoded_bytes = credentials.encode("utf-8")
        b64_credentials = base64.b64encode(encoded_bytes).decode("utf-8")
        return f"Basic {b64_credentials}"

    async def _refresh_token(self) -> None:
        """Refresh the access token using refresh token."""
        if not self.token.get("refresh_token"):
            raise RuntimeError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.token["refresh_token"],
        }
        headers = {
            "Authorization": self._basic_client_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            new_token = response.json()
            refresh_token = new_token.get(
                "refresh_token", self.token.get("refresh_token")
            )
            self.token.update({
                "access_token": new_token["access_token"],
                "token_type": new_token.get("token_type", "bearer"),
                "expires_in": new_token.get("expires_in", 3600),
                "refresh_token": refresh_token,
                "scope": new_token.get("scope", self.token.get("scope")),
                "obtained_at": int(time.time()),
            })
            TokenStorage.save_token(self.token)

    def _interactive_login(self) -> str:
        """Perform interactive OAuth login to get authorization code."""
        state = os.urandom(12).hex()
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": self.config.scopes,
            "state": state,
            "prompt": "consent",
        }
        auth_url = f"{self.auth_endpoint}?{urlencode(params)}"

        print(f"\nOpen this URL to authorize:\n{auth_url}\n")

        # Try to open browser
        with contextlib.suppress(Exception):
            webbrowser.open(auth_url, new=2)

        # Start local server to capture the code
        code_holder = {}
        redirect_uri = self.config.redirect_uri

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_url = urlparse(self.path)
                redirect_path = urlparse(redirect_uri).path

                if parsed_url.path != redirect_path:
                    self.send_response(404)
                    self.end_headers()
                    return

                query_params = parse_qs(parsed_url.query)

                if "error" in query_params:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Authorization error.")
                    return

                if query_params.get("state", [""])[0] != state:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"State mismatch.")
                    return

                code_holder["code"] = query_params.get("code", [""])[0]
                self.send_response(200)
                self.end_headers()
                message = b"You can close this tab and return to the app."
                self.wfile.write(message)

            def log_message(self, *args, **kwargs):
                pass  # Silence logs

        # Parse redirect URI for server setup
        redirect_parsed = urlparse(self.config.redirect_uri)
        host = redirect_parsed.hostname or "127.0.0.1"
        port = redirect_parsed.port or 8765

        httpd = HTTPServer((host, port), CallbackHandler)

        thread = threading.Thread(target=httpd.handle_request, daemon=True)
        thread.start()
        thread.join(timeout=300)

        if "code" not in code_holder:
            httpd.server_close()
            error_msg = (
                "Did not receive authorization code. "
                "Check redirect URI configuration."
            )
            raise RuntimeError(error_msg)

        code = code_holder["code"]
        httpd.server_close()
        return code

    async def _exchange_code_for_tokens(self, code: str) -> None:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }
        headers = {
            "Authorization": self._basic_client_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            self.token = {
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "bearer"),
                "expires_in": token_data.get("expires_in", 3600),
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data.get("scope", self.config.scopes),
                "obtained_at": int(time.time()),
            }
            TokenStorage.save_token(self.token)

    async def ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        if self._have_valid_access_token():
            return

        if self.token.get("refresh_token"):
            try:
                await self._refresh_token()
                return
            except Exception as e:
                warning_msg = "Token refresh failed, starting new auth flow"
                logger.warning(warning_msg, error=str(e))

        # Perform full OAuth flow (this would need user interaction)
        # For MCP server, we should require pre-authorized tokens
        error_msg = (
            "No valid access token available. "
            "Please run interactive authentication first."
        )
        raise RuntimeError(error_msg)

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        await self.ensure_valid_token()
        return {"Authorization": f"Bearer {self.token['access_token']}"}


class EmplifiBasicClient(EmplifiAuthClient):
    """Basic authentication client for Emplifi API."""

    def __init__(self, config: EmplifiConfig):
        super().__init__(config)
        if not (config.basic_token and config.basic_secret):
            raise ValueError("Basic auth requires both token and secret")

        credentials = f"{config.basic_token}:{config.basic_secret}"
        encoded_bytes = credentials.encode("utf-8")
        b64_credentials = base64.b64encode(encoded_bytes).decode("utf-8")
        self._auth_header = {"Authorization": f"Basic {b64_credentials}"}

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        return self._auth_header


# Utility functions
def _get_config() -> EmplifiConfig:
    """Get Emplifi configuration from environment variables."""
    # Ensure environment variables are loaded from .env file
    load_environment()

    return EmplifiConfig(
        client_id=os.environ.get("EMPLIFI_CLIENT_ID"),
        client_secret=os.environ.get("EMPLIFI_CLIENT_SECRET"),
        redirect_uri=os.environ.get("EMPLIFI_REDIRECT_URI"),
        scopes=os.environ.get("EMPLIFI_SCOPES", "api.read offline_access"),
        basic_token=os.environ.get("EMPLIFI_TOKEN"),
        basic_secret=os.environ.get("EMPLIFI_SECRET"),
    )


def _get_auth_client() -> EmplifiAuthClient:
    """Get appropriate authentication client based on configuration."""
    config = _get_config()

    # Prefer OAuth if configured
    if config.client_id and config.client_secret and config.redirect_uri:
        return EmplifiOAuthClient(config)

    # Fall back to Basic auth
    if config.basic_token and config.basic_secret:
        return EmplifiBasicClient(config)

    raise ValueError(
        "No authentication configured. Set either OAuth credentials "
        "(EMPLIFI_CLIENT_ID, EMPLIFI_CLIENT_SECRET, EMPLIFI_REDIRECT_URI) "
        "or Basic auth credentials (EMPLIFI_TOKEN, EMPLIFI_SECRET)"
    )


# MCP Tool Functions
async def list_listening_queries() -> list[ListeningQuery]:
    """List all available listening queries from Emplifi.

    Returns a list of listening queries that can be used to fetch posts
    and metrics.
    """
    client = _get_auth_client()
    headers = await client.get_auth_headers()

    url = f"{API_BASE}/3/listening/queries"

    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        data = response.json()
        queries = data.get("queries", [])

        return [
            ListeningQuery(
                id=query["id"],
                name=query.get("name", ""),
                description=query.get("description"),
                status=query.get("status")
            )
            for query in queries
        ]


async def fetch_listening_posts(
    query_ids: Annotated[list[str], "List of listening query IDs"],
    date_start: Annotated[str, "Start date in YYYY-MM-DD format"],
    date_end: Annotated[str, "End date in YYYY-MM-DD format"],
    fields: Annotated[list[str] | None, "Fields to include"] = None,
    limit: Annotated[int, "Number of posts per page (max 100)"] = 100,
    filters: Annotated[list[PostsFilter] | None, "Filters"] = None,
    sort: Annotated[list[PostsSort] | None, "Sort config"] = None,
    max_pages: Annotated[int, "Maximum number of pages"] = 1,
) -> list[ListeningPost]:
    """Fetch listening posts (mentions) for specified queries and date range.

    This tool retrieves social media posts and mentions that match your
    listening queries. It supports pagination, filtering, and sorting.
    """
    client = _get_auth_client()
    headers = await client.get_auth_headers()

    url = f"{API_BASE}/3/listening/posts"

    # Default fields if not specified (based on API documentation)
    if fields is None:
        fields = [
            "id", "created_time", "platform", "author",
            "message", "sentiment", "interactions", "url"
        ]

    # Default sort if not specified
    # Posts API allows: comments, potential_impressions, interactions, shares
    if sort is None:
        sort = [PostsSort(field="interactions", order="desc")]

    # Convert date strings to simple YYYY-MM-DD format (posts API requirement)
    def format_date(date_str: str) -> str:
        if "T" in date_str:
            # ISO format, extract date part only
            return date_str.split("T")[0]
        return date_str  # Already in YYYY-MM-DD format

    payload = {
        "listening_queries": query_ids,
        "date_start": format_date(date_start),
        "date_end": format_date(date_end),
        "limit": min(limit, 100),  # API max is 100
        "fields": fields,
    }

    if filters:
        payload["filter"] = [f.model_dump() for f in filters]

    if sort:
        payload["sort"] = [s.model_dump() for s in sort]

    posts = []
    page = 0
    next_cursor = None

    logger.info(f"Fetching posts with payload: {payload}")

    async with httpx.AsyncClient() as http_client:
        while page < max_pages:
            body = dict(payload)
            if next_cursor:
                body["after"] = next_cursor  # Use "after" for pagination

            try:
                response = await http_client.post(
                    url,
                    headers={**headers, "Content-Type": "application/json"},
                    json=body,
                    timeout=120
                )
                response.raise_for_status()

                response_data = response.json()
                logger.info(
                    f"API response structure: {list(response_data.keys())}"
                )

                # Check if request was successful
                if not response_data.get("success", False):
                    logger.error(
                        f"API returned unsuccessful response: {response_data}"
                    )
                    break

                # Get data object from response
                data = response_data.get("data", {})
                page_posts = data.get("posts", [])

                logger.info(f"Page {page + 1}: Found {len(page_posts)} posts")

                for post in page_posts:
                    try:
                        posts.append(ListeningPost(
                            id=post["id"],
                            created_time=post.get("created_time", ""),
                            platform=post.get("platform", ""),
                            author=post.get("author", {}),
                            message=post.get("message", ""),
                            sentiment=post.get("sentiment"),
                            interactions=post.get("interactions", 0)
                        ))
                    except Exception as e:
                        post_id = post.get("id", "unknown")
                        logger.error(f"Error parsing post {post_id}: {e}")
                        continue

                # Get next cursor for pagination
                next_cursor = data.get("next")
                page += 1

                if not next_cursor or len(page_posts) == 0:
                    break

            except Exception as e:
                logger.error(f"Error fetching posts page {page + 1}: {e}")
                break

    logger.info(f"Successfully fetched {len(posts)} posts")
    return posts


async def fetch_listening_metrics(
    query_ids: Annotated[list[str], "List of listening query IDs"],
    date_start: Annotated[str, "Start date in YYYY-MM-DD format"],
    date_end: Annotated[str, "End date in YYYY-MM-DD format"],
    metrics: Annotated[list[MetricConfig], "Metrics to fetch"],
    dimensions: Annotated[list[DimensionConfig] | None, "Dimensions"] = None,
    filters: Annotated[list[PostsFilter] | None, "Filters"] = None,
) -> ListeningMetrics:
    """Fetch listening metrics for specified queries and date range.

    This tool retrieves aggregated metrics about your listening queries,
    such as mention counts, sentiment distribution, and engagement metrics.
    """
    client = _get_auth_client()
    headers = await client.get_auth_headers()

    url = f"{API_BASE}/3/listening/metrics"

    # Convert date strings to ISO format if they're simple dates
    def format_date(date_str: str) -> str:
        if "T" not in date_str:
            # Simple date format, convert to ISO
            if date_str == date_start:
                return f"{date_str}T00:00:00"
            else:
                return f"{date_str}T23:59:59"
        return date_str

    payload = {
        "listening_queries": query_ids,
        "date_start": format_date(date_start),
        "date_end": format_date(date_end),
        "metrics": [m.model_dump() for m in metrics],
    }

    if dimensions:
        payload["dimensions"] = [d.model_dump() for d in dimensions]

    if filters:
        payload["filter"] = [f.model_dump() for f in filters]

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        data = response.json()
        return ListeningMetrics(
            data=data.get("data", []),
            meta=data.get("meta")
        )


# Convenience tools for common use cases
async def get_recent_posts(
    query_id: Annotated[str, "Listening query ID"],
    days_back: Annotated[int, "Number of days back to fetch posts"] = 7,
    limit_per_page: Annotated[int, "Posts per page"] = 50,
    max_pages: Annotated[int, "Maximum pages to fetch"] = 2,
) -> list[ListeningPost]:
    """Get recent posts for a specific listening query.

    This is a convenience tool that fetches posts from the last N days
    for a single listening query with sensible defaults.
    """
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days_back)

    return await fetch_listening_posts(
        query_ids=[query_id],
        date_start=start_date.strftime("%Y-%m-%d"),
        date_end=end_date.strftime("%Y-%m-%d"),
        limit=limit_per_page,
        max_pages=max_pages,
        sort=[PostsSort(field="created_time", order="desc")]
    )


async def get_daily_mention_metrics(
    query_id: Annotated[str, "Listening query ID"],
    days_back: Annotated[int, "Number of days back to analyze"] = 30,
) -> ListeningMetrics:
    """Get daily mention count metrics for a listening query.

    This convenience tool fetches mention count metrics grouped by day
    for the specified time period.
    """
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days_back)

    return await fetch_listening_metrics(
        query_ids=[query_id],
        date_start=start_date.strftime("%Y-%m-%d"),
        date_end=end_date.strftime("%Y-%m-%d"),
        metrics=[MetricConfig(metric="content_count")],
        dimensions=[DimensionConfig(type="date.day")]
    )
