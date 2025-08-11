"""Configuration management for the MCP server."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from mcp_server.models import ServerConfig


ENV_FILE_CANDIDATES = [
    ".env",
    ".env.local",
]


def load_environment() -> None:
    """Load environment variables from the first existing .env file (if any)."""
    for candidate in ENV_FILE_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            load_dotenv(path)
            break


def _coerce_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_config() -> ServerConfig:
    """Return cached server configuration built from environment variables."""
    load_environment()
    return ServerConfig(
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "8000")),
        path=os.getenv("MCP_PATH", "/mcp"),
        debug=_coerce_bool(os.getenv("MCP_DEBUG"), False),
        log_level=os.getenv("MCP_LOG_LEVEL", "INFO").upper(),
    )
