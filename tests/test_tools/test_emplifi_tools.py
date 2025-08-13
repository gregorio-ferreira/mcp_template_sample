"""Tests for simplified Emplifi Listening API tools."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import Response

from mcp_server.tools.emplifi_tools import (
    ListeningPost,
    ListeningQuery,
    _get_auth_headers,
    fetch_listening_posts,
    get_recent_posts,
    list_listening_queries,
)

# Test constants
TEST_QUERY_ID = "LNQ_1140092_641afbbd98a766f5eb4a4915"
TEST_TOKEN = "test_token"
TEST_SECRET = "test_secret"


class TestAuthentication:
    """Test authentication functionality."""

    def test_get_auth_headers_success(self):
        """Test building auth headers with valid credentials."""
        with patch(
            "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
            return_value=(TEST_TOKEN, TEST_SECRET),
        ):
            headers = _get_auth_headers()

            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Basic ")
            assert "Content-Type" in headers
            assert headers["Content-Type"] == "application/json"

    def test_get_auth_headers_missing_credentials(self):
        """Test auth headers fail with missing credentials."""
        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(None, None),
            ),
            pytest.raises(ValueError, match="Missing Emplifi credentials"),
        ):
            _get_auth_headers()


class TestListeningQueries:
    """Test listing queries functionality."""

    @pytest.mark.asyncio
    async def test_list_listening_queries_success(self):
        """Test successful query listing."""
        mock_response_data = {
            "data": [
                {
                    "id": TEST_QUERY_ID,
                    "name": "Test Query",
                    "description": "A test query",
                    "status": "active",
                }
            ]
        }

        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_response_data

        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(TEST_TOKEN, TEST_SECRET),
            ),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            queries = await list_listening_queries()

            assert len(queries) == 1
            assert isinstance(queries[0], ListeningQuery)
            assert queries[0].id == TEST_QUERY_ID
            assert queries[0].name == "Test Query"


class TestFetchingPosts:
    """Test fetching posts functionality."""

    @pytest.mark.asyncio
    async def test_fetch_listening_posts_success(self):
        """Test successful post fetching."""
        mock_response_data = {
            "data": {
                "posts": [
                    {
                        "id": "post_123",
                        "created_time": "2025-08-01T10:00:00Z",
                        "platform": "twitter",
                        "author": {"name": "test_user"},
                        "message": "Test message",
                        "sentiment": "positive",
                        "interactions": 10,
                        "url": "https://example.com",
                    }
                ],
                "next": None,
            }
        }

        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_response_data

        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(TEST_TOKEN, TEST_SECRET),
            ),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_post = AsyncMock(return_value=mock_response)
            mock_ctx = mock_client.return_value.__aenter__.return_value
            mock_ctx.post = mock_post

            posts = await fetch_listening_posts(
                query_ids=[TEST_QUERY_ID], date_start="2025-08-01", date_end="2025-08-02"
            )

            assert len(posts) == 1
            assert isinstance(posts[0], ListeningPost)
            assert posts[0].id == "post_123"
            assert posts[0].platform == "twitter"
            assert posts[0].sentiment == "positive"

    @pytest.mark.asyncio
    async def test_get_recent_posts_success(self):
        """Test convenience function for recent posts."""
        mock_response_data = {
            "data": {
                "posts": [
                    {
                        "id": "recent_post",
                        "created_time": "2025-08-10T10:00:00Z",
                        "platform": "instagram",
                        "author": {"name": "recent_user"},
                        "message": "Recent post",
                    }
                ],
                "next": None,
            }
        }

        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = mock_response_data

        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(TEST_TOKEN, TEST_SECRET),
            ),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_post = AsyncMock(return_value=mock_response)
            mock_ctx = mock_client.return_value.__aenter__.return_value
            mock_ctx.post = mock_post

            posts = await get_recent_posts(query_id=TEST_QUERY_ID, days_back=7, limit=50)

            assert len(posts) == 1
            assert posts[0].id == "recent_post"


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_missing_credentials(self):
        """Test behavior with missing credentials."""
        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(None, None),
            ),
            pytest.raises(ValueError),
        ):
            await list_listening_queries()

    @pytest.mark.asyncio
    async def test_http_error(self):
        """Test HTTP error handling."""
        mock_response = AsyncMock(spec=Response)
        mock_response.raise_for_status.side_effect = RuntimeError("HTTP 401")

        with (
            patch(
                "mcp_server.tools.emplifi_tools.get_emplifi_credentials",
                return_value=(TEST_TOKEN, TEST_SECRET),
            ),
            patch("httpx.AsyncClient") as mock_client,
        ):
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            with pytest.raises(RuntimeError):
                await list_listening_queries()
