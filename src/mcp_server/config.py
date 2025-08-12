"""Configuration management for the MCP server.

This module centralizes loading of environment variables and provides a single
entry point for accessing server configuration throughout the project. Values
are sourced from the process environment with optional loading from a ``.env``
file. The resulting configuration is cached for efficiency.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from mcp_server.models import ServerConfig

ENV_FILE_CANDIDATES = [".env", ".env.local"]


def load_environment() -> None:
    """Load environment variables from the first existing ``.env`` file.

    The search stops at the first file found in :data:`ENV_FILE_CANDIDATES`.
    Existing environment variables take precedence over file values.
    """

    for candidate in ENV_FILE_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            load_dotenv(path)
            break


def _coerce_bool(value: str | None, default: bool = False) -> bool:
    """Return a boolean from a string value."""

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


def get_server_url() -> str:
    """Return the full HTTP URL for the MCP server based on configuration."""

    cfg = get_config()
    path = cfg.path if cfg.path.startswith("/") else f"/{cfg.path}"
    if not path.endswith("/"):
        path = f"{path}/"
    return f"http://{cfg.host}:{cfg.port}{path}"


__all__ = ["get_config", "get_server_url", "load_environment"]
