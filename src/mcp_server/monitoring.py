"""Performance monitoring utilities for the MCP server."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def monitor_performance(func: Callable[P, R]) -> Callable[P, R]:  # noqa: UP047
    """Decorator to monitor function performance."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
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

    return wrapper


def monitor_async_performance(  # noqa: UP047
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Decorator to monitor async function performance."""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
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

    return wrapper
