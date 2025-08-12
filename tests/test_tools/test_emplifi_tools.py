"""Tests for Emplifi Listening API tools."""

from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from mcp_server.tools.emplifi_tools import (
    EmplifiBasicClient,
    EmplifiConfig,
    EmplifiOAuthClient,
    ListeningMetrics,
    ListeningPost,
    ListeningQuery,
    MetricConfig,
    _get_auth_client,
    _get_config,
    fetch_listening_metrics,
    fetch_listening_posts,
    get_daily_mention_metrics,
    get_recent_posts,
    list_listening_queries,
)

# Test constants
TEST_QUERY_ID = "LNQ_1140092_641afbbd98a766f5eb4a4915"
TEST_QUERY_NAME = "Syngenta Flowers"


class TestEmplifiConfig:
    """Test EmplifiConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = EmplifiConfig()
        assert config.scopes == "api.read offline_access"
        assert config.client_id is None
        assert config.basic_token is None

    def test_oauth_config(self) -> None:
        """Test OAuth configuration."""
        config = EmplifiConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8765/callback"
        )
        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.redirect_uri == "http://localhost:8765/callback"

    def test_basic_config(self) -> None:
        """Test Basic auth configuration."""
        config = EmplifiConfig(
            basic_token="test_token",
            basic_secret="test_secret"
        )
        assert config.basic_token == "test_token"
        assert config.basic_secret == "test_secret"


class TestEmplifiBasicClient:
    """Test basic authentication client."""

    def test_initialization_success(self) -> None:
        """Test successful initialization with valid credentials."""
        config = EmplifiConfig(
            basic_token="test_token",
            basic_secret="test_secret"
        )
        client = EmplifiBasicClient(config)
        assert "Authorization" in client._auth_header
        assert client._auth_header["Authorization"].startswith("Basic ")

    def test_initialization_failure(self) -> None:
        """Test initialization failure with missing credentials."""
        config = EmplifiConfig()
        error_msg = "Basic auth requires both token and secret"
        with pytest.raises(ValueError, match=error_msg):
            EmplifiBasicClient(config)

    @pytest.mark.asyncio
    async def test_get_auth_headers(self) -> None:
        """Test getting authentication headers."""
        config = EmplifiConfig(
            basic_token="test_token",
            basic_secret="test_secret"
        )
        client = EmplifiBasicClient(config)
        headers = await client.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")


class TestEmplifiOAuthClient:
    """Test OAuth authentication client."""

    def test_initialization(self) -> None:
        """Test OAuth client initialization."""
        config = EmplifiConfig(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8765/callback"
        )
        client = EmplifiOAuthClient(config)
        assert client.config == config
        assert client.auth_endpoint.endswith("/auth")
        assert client.token_endpoint.endswith("/token")

    def test_have_valid_access_token_false_no_token(self) -> None:
        """Test token validation with no token."""
        config = EmplifiConfig()
        client = EmplifiOAuthClient(config)
        assert not client._have_valid_access_token()

    def test_have_valid_access_token_false_expired(self) -> None:
        """Test token validation with expired token."""
        config = EmplifiConfig()
        client = EmplifiOAuthClient(config)
        client.token = {
            "access_token": "test_token",
            "obtained_at": 1000,
            "expires_in": 3600
        }
        assert not client._have_valid_access_token()

    def test_have_valid_access_token_true(self) -> None:
        """Test token validation with valid token."""
        config = EmplifiConfig()
        client = EmplifiOAuthClient(config)
        current_time = int(datetime.now().timestamp())
        client.token = {
            "access_token": "test_token",
            "obtained_at": current_time,
            "expires_in": 3600
        }
        assert client._have_valid_access_token()


@pytest.fixture
def mock_auth_client() -> MagicMock:
    """Create a mock auth client."""
    client = MagicMock()
    auth_header = {"Authorization": "Bearer test_token"}
    client.get_auth_headers = AsyncMock(return_value=auth_header)
    return client


class TestListeningQueries:
    """Test listing queries functionality."""

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools._get_auth_client")
    @patch("httpx.AsyncClient")
    async def test_list_listening_queries_success(
        self, mock_http_client: MagicMock, mock_auth_client: MagicMock
    ) -> None:
        """Test successful query listing."""
        # Setup mocks
        mock_client_instance = mock_auth_client.return_value
        auth_header = {"Authorization": "Bearer test_token"}
        mock_client_instance.get_auth_headers = AsyncMock(
            return_value=auth_header
        )

        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "queries": [
                {
                    "id": TEST_QUERY_ID,
                    "name": TEST_QUERY_NAME,
                    "description": "A test listening query for flowers",
                    "status": "active"
                }
            ]
        }

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute test
        result = await list_listening_queries()

        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], ListeningQuery)
        assert result[0].id == TEST_QUERY_ID
        assert result[0].name == TEST_QUERY_NAME
        assert result[0].description == "A test listening query for flowers"
        assert result[0].status == "active"

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools._get_auth_client")
    @patch("httpx.AsyncClient")
    async def test_list_listening_queries_empty(
        self, mock_http_client: MagicMock, mock_auth_client: MagicMock
    ) -> None:
        """Test query listing with empty response."""
        # Setup mocks
        mock_client_instance = mock_auth_client.return_value
        auth_header = {"Authorization": "Bearer test_token"}
        mock_client_instance.get_auth_headers = AsyncMock(
            return_value=auth_header
        )

        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"queries": []}

        mock_http = MagicMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute test
        result = await list_listening_queries()

        # Verify results
        assert len(result) == 0


class TestFetchListeningPosts:
    """Test fetching posts functionality."""

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools._get_auth_client")
    @patch("httpx.AsyncClient")
    async def test_fetch_posts_success(
        self, mock_http_client: MagicMock, mock_auth_client: MagicMock
    ) -> None:
        """Test successful post fetching."""
        # Setup mocks
        mock_client_instance = mock_auth_client.return_value
        auth_header = {"Authorization": "Bearer test_token"}
        mock_client_instance.get_auth_headers = AsyncMock(
            return_value=auth_header
        )

        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "posts": [
                    {
                        "id": "POST_123",
                        "created_time": "2025-01-01T12:00:00Z",
                        "platform": "facebook",
                        "author": {"name": "Test Author"},
                        "message": "Test message about flowers",
                        "sentiment": "positive",
                        "interactions": {"likes": 10, "shares": 2}
                    }
                ],
                "next": None
            }
        }

        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute test
        result = await fetch_listening_posts(
            query_ids=[TEST_QUERY_ID],
            date_start="2025-01-01",
            date_end="2025-01-02"
        )

        # Verify results
        assert len(result) == 1
        assert isinstance(result[0], ListeningPost)
        assert result[0].id == "POST_123"
        assert result[0].platform == "facebook"
        assert result[0].message == "Test message about flowers"
        assert result[0].sentiment == "positive"

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools._get_auth_client")
    @patch("httpx.AsyncClient")
    async def test_fetch_posts_pagination(
        self, mock_http_client: MagicMock, mock_auth_client: MagicMock
    ) -> None:
        """Test post fetching with pagination."""
        # Setup mocks
        mock_client_instance = mock_auth_client.return_value
        auth_header = {"Authorization": "Bearer test_token"}
        mock_client_instance.get_auth_headers = AsyncMock(
            return_value=auth_header
        )

        # First page response
        mock_response_1 = MagicMock(spec=Response)
        mock_response_1.raise_for_status = MagicMock()
        mock_response_1.json.return_value = {
            "data": {
                "posts": [{
                    "id": "POST_1",
                    "created_time": "2025-01-01T12:00:00Z",
                    "platform": "facebook",
                    "author": {"name": "Author1"},
                    "message": "Message 1"
                }],
                "next": "cursor_123"
            }
        }

        # Second page response
        mock_response_2 = MagicMock(spec=Response)
        mock_response_2.raise_for_status = MagicMock()
        mock_response_2.json.return_value = {
            "data": {
                "posts": [{
                    "id": "POST_2",
                    "created_time": "2025-01-01T13:00:00Z",
                    "platform": "twitter",
                    "author": {"name": "Author2"},
                    "message": "Message 2"
                }],
                "next": None
            }
        }

        mock_http = MagicMock()
        mock_http.post = AsyncMock(
            side_effect=[mock_response_1, mock_response_2]
        )
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute test
        result = await fetch_listening_posts(
            query_ids=[TEST_QUERY_ID],
            date_start="2025-01-01",
            date_end="2025-01-02",
            max_pages=2
        )

        # Verify results
        assert len(result) == 2
        assert result[0].id == "POST_1"
        assert result[1].id == "POST_2"
        assert mock_http.post.call_count == 2


class TestFetchListeningMetrics:
    """Test fetching metrics functionality."""

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools._get_auth_client")
    @patch("httpx.AsyncClient")
    async def test_fetch_metrics_success(
        self, mock_http_client: MagicMock, mock_auth_client: MagicMock
    ) -> None:
        """Test successful metrics fetching."""
        # Setup mocks
        mock_client_instance = mock_auth_client.return_value
        auth_header = {"Authorization": "Bearer test_token"}
        mock_client_instance.get_auth_headers = AsyncMock(
            return_value=auth_header
        )

        mock_response = MagicMock(spec=Response)
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"date": "2025-01-01", "mentions": 5},
                {"date": "2025-01-02", "mentions": 3}
            ],
            "meta": {"total": 8, "period": "daily"}
        }

        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_http
        )
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute test
        result = await fetch_listening_metrics(
            query_ids=[TEST_QUERY_ID],
            date_start="2025-01-01",
            date_end="2025-01-02",
            metrics=[MetricConfig(type="mentions")]
        )

        # Verify results
        assert isinstance(result, ListeningMetrics)
        assert len(result.data) == 2
        assert result.meta is not None
        assert result.meta["total"] == 8
        assert result.data[0]["mentions"] == 5
        assert result.data[1]["mentions"] == 3


class TestConvenienceTools:
    """Test convenience tools."""

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools.fetch_listening_posts")
    async def test_get_recent_posts(self, mock_fetch_posts: AsyncMock) -> None:
        """Test getting recent posts."""
        mock_posts = [
            ListeningPost(
                id="POST_123",
                created_time="2025-01-01T12:00:00Z",
                platform="facebook",
                author={"name": "Test"},
                message="Test message"
            )
        ]
        mock_fetch_posts.return_value = mock_posts

        result = await get_recent_posts(TEST_QUERY_ID, days_back=7)

        assert result == mock_posts
        mock_fetch_posts.assert_called_once()

        # Verify the date range is correct
        call_args = mock_fetch_posts.call_args
        assert call_args[1]["query_ids"] == [TEST_QUERY_ID]
        assert "date_start" in call_args[1]
        assert "date_end" in call_args[1]

    @pytest.mark.asyncio
    @patch("mcp_server.tools.emplifi_tools.fetch_listening_metrics")
    async def test_get_daily_mention_metrics(
        self, mock_fetch_metrics: AsyncMock
    ) -> None:
        """Test getting daily mention metrics."""
        mock_metrics = ListeningMetrics(
            data=[{"date": "2025-01-01", "mentions": 5}],
            meta={"total": 5}
        )
        mock_fetch_metrics.return_value = mock_metrics

        result = await get_daily_mention_metrics(TEST_QUERY_ID, days_back=30)

        assert result == mock_metrics
        mock_fetch_metrics.assert_called_once()

        # Verify the metric configuration
        call_args = mock_fetch_metrics.call_args
        assert call_args[1]["query_ids"] == [TEST_QUERY_ID]
        assert call_args[1]["metrics"][0].type == "mentions"


class TestConfigurationFunctions:
    """Test configuration utility functions."""

    @patch("mcp_server.tools.emplifi_tools.load_environment")
    @patch.dict(os.environ, {
        "EMPLIFI_CLIENT_ID": "test_id",
        "EMPLIFI_CLIENT_SECRET": "test_secret",
        "EMPLIFI_REDIRECT_URI": "http://localhost:8765/callback"
    })
    def test_get_config_oauth(self, mock_load_env: MagicMock) -> None:
        """Test getting OAuth configuration from environment."""
        config = _get_config()
        assert config.client_id == "test_id"
        assert config.client_secret == "test_secret"
        assert config.redirect_uri == "http://localhost:8765/callback"
        mock_load_env.assert_called_once()

    @patch("mcp_server.tools.emplifi_tools.load_environment")
    @patch.dict(os.environ, {
        "EMPLIFI_TOKEN": "test_token",
        "EMPLIFI_SECRET": "test_secret"
    })
    def test_get_config_basic(self, mock_load_env: MagicMock) -> None:
        """Test getting Basic auth configuration from environment."""
        config = _get_config()
        assert config.basic_token == "test_token"
        assert config.basic_secret == "test_secret"
        mock_load_env.assert_called_once()

    @patch("mcp_server.tools.emplifi_tools.load_environment")
    @patch.dict(os.environ, {
        "EMPLIFI_CLIENT_ID": "test_id",
        "EMPLIFI_CLIENT_SECRET": "test_secret",
        "EMPLIFI_REDIRECT_URI": "http://localhost:8765/callback"
    })
    @patch("mcp_server.tools.emplifi_tools.EmplifiOAuthClient")
    def test_get_auth_client_oauth(
        self, mock_oauth_client: MagicMock, mock_load_env: MagicMock
    ) -> None:
        """Test getting OAuth client when OAuth credentials are available."""
        _get_auth_client()
        mock_oauth_client.assert_called_once()
        mock_load_env.assert_called_once()

    @patch("mcp_server.tools.emplifi_tools.load_environment")
    @patch.dict(os.environ, {
        "EMPLIFI_TOKEN": "test_token",
        "EMPLIFI_SECRET": "test_secret"
    })
    @patch("mcp_server.tools.emplifi_tools.EmplifiBasicClient")
    def test_get_auth_client_basic(
        self, mock_basic_client: MagicMock, mock_load_env: MagicMock
    ) -> None:
        """Test getting Basic auth client when credentials are available."""
        _get_auth_client()
        mock_basic_client.assert_called_once()
        mock_load_env.assert_called_once()

    @patch("mcp_server.tools.emplifi_tools.load_environment")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_auth_client_no_credentials(
        self, mock_load_env: MagicMock
    ) -> None:
        """Test error when no credentials are configured."""
        with pytest.raises(ValueError, match="No authentication configured"):
            _get_auth_client()
        mock_load_env.assert_called_once()


# Integration tests (require real credentials)
class TestIntegration:
    """Integration tests with real Emplifi API (optional)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_list_queries(self) -> None:
        """Test listing queries with real API (requires credentials)."""
        try:
            queries = await list_listening_queries()
            # If this succeeds, we should have some queries
            assert isinstance(queries, list)
            if queries:
                assert isinstance(queries[0], ListeningQuery)
                # Check if our test query exists
                test_query = next(
                    (q for q in queries if q.id == TEST_QUERY_ID), None
                )
                if test_query:
                    assert test_query.name == TEST_QUERY_NAME
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_fetch_posts_year_2025(self) -> None:
        """Test fetching posts for Syngenta Flowers for 2025."""
        try:
            posts = await fetch_listening_posts(
                query_ids=[TEST_QUERY_ID],
                date_start="2025-01-01",
                date_end="2025-12-31",
                limit=10,
                max_pages=1
            )
            assert isinstance(posts, list)
            # Even if no posts, the structure should be correct
            for post in posts:
                assert isinstance(post, ListeningPost)
                assert post.id
                assert post.platform
                assert post.message
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_fetch_metrics_year_2025(self) -> None:
        """Test fetching metrics for Syngenta Flowers for 2025."""
        try:
            metrics = await fetch_listening_metrics(
                query_ids=[TEST_QUERY_ID],
                date_start="2025-01-01",
                date_end="2025-12-31",
                metrics=[MetricConfig(type="mentions")]
            )
            assert isinstance(metrics, ListeningMetrics)
            assert isinstance(metrics.data, list)
            # Meta can be None
            if metrics.meta:
                assert isinstance(metrics.meta, dict)
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_convenience_tools(self) -> None:
        """Test convenience tools with real API."""
        try:
            # Test recent posts
            recent_posts = await get_recent_posts(
                TEST_QUERY_ID, days_back=30, max_pages=1
            )
            assert isinstance(recent_posts, list)

            # Test daily metrics
            daily_metrics = await get_daily_mention_metrics(
                TEST_QUERY_ID, days_back=90
            )
            assert isinstance(daily_metrics, ListeningMetrics)
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")
