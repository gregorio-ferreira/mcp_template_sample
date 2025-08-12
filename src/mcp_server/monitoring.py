"""Performance monitoring utilities for the MCP server."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def monitor_performance(func: F) -> F:
    """Decorator to monitor function performance."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start_time
            logger.info(
                "Function %s completed in %.2fms",
                func.__name__,
                duration * 1000,
            )

    return wrapper  # type: ignore[return-value]


def monitor_async_performance(func: F) -> F:
    """Decorator to monitor async function performance."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.perf_counter() - start_time
            logger.info(
                "Async function %s completed in %.2fms",
                func.__name__,
                duration * 1000,
            )

    return wrapper  # type: ignore[return-value]
