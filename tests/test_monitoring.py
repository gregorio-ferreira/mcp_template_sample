"""Tests for monitoring utilities."""

import asyncio
import time
from unittest.mock import patch

import pytest

from mcp_server.monitoring import monitor_async_performance, monitor_performance


def test_monitor_performance() -> None:
    """Test performance monitoring decorator."""

    @monitor_performance
    def slow_function(duration: float) -> str:
        """Test function that sleeps."""
        time.sleep(duration)
        return "completed"

    with patch("mcp_server.monitoring.logger") as mock_logger:
        result = slow_function(0.01)  # 10ms

        assert result == "completed"
        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        assert "slow_function" in args[1]
        assert "completed in" in args[0]


@pytest.mark.asyncio
async def test_monitor_async_performance() -> None:
    """Test async performance monitoring decorator."""

    @monitor_async_performance
    async def async_slow_function(duration: float) -> str:
        """Test async function that sleeps."""
        await asyncio.sleep(duration)
        return "async completed"

    with patch("mcp_server.monitoring.logger") as mock_logger:
        result = await async_slow_function(0.01)  # 10ms

        assert result == "async completed"
        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        assert "async_slow_function" in args[1]
        assert "Async function" in args[0]


def test_monitor_performance_with_exception() -> None:
    """Test that performance monitoring still logs when function raises exception."""

    @monitor_performance
    def failing_function() -> None:
        """Function that raises an exception."""
        raise ValueError("test error")

    with patch("mcp_server.monitoring.logger") as mock_logger:
        with pytest.raises(ValueError, match="test error"):
            failing_function()

        # Should still log performance even when exception is raised
        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        assert "failing_function" in args[1]


@pytest.mark.asyncio
async def test_monitor_async_performance_with_exception() -> None:
    """Test that async performance monitoring still logs when function raises exception."""

    @monitor_async_performance
    async def async_failing_function() -> None:
        """Async function that raises an exception."""
        raise ValueError("async test error")

    with patch("mcp_server.monitoring.logger") as mock_logger:
        with pytest.raises(ValueError, match="async test error"):
            await async_failing_function()

        # Should still log performance even when exception is raised
        mock_logger.info.assert_called_once()
        args = mock_logger.info.call_args[0]
        assert "async_failing_function" in args[1]
