"""Core configuration utilities for the MCP server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_CANDIDATES = [".env", ".env.local"]


class ServerSettings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    # MCP Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    debug: bool = False
    log_level: str = "INFO"

    # Emplifi API credentials
    emplifi_token: str | None = None
    emplifi_secret: str | None = None
    emplifi_api_base: str = "https://api.emplifi.io/3"
    emplifi_timeout: int = 30

    # OpenAI API credentials (for AI-powered chat agent)
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="",  # No prefix to allow direct env var names
        case_sensitive=False,
        env_file=".env",
        extra="ignore",  # Ignore extra environment variables
    )

    def __init__(self, **data: Any) -> None:
        """Initialize settings with support for MCP_ prefixed variables."""
        super().__init__(**data)

        # Override with MCP_ prefixed values if they exist
        import os

        if os.getenv("MCP_HOST"):
            self.host = os.getenv("MCP_HOST", self.host)
        if os.getenv("MCP_PORT"):
            self.port = int(os.getenv("MCP_PORT", str(self.port)))
        if os.getenv("MCP_PATH"):
            self.path = os.getenv("MCP_PATH", self.path)
        if os.getenv("MCP_DEBUG"):
            debug_val = os.getenv("MCP_DEBUG", "").lower()
            self.debug = debug_val in ("true", "1", "yes")
        if os.getenv("MCP_LOG_LEVEL"):
            self.log_level = os.getenv("MCP_LOG_LEVEL", self.log_level)


def load_environment() -> None:
    """Load environment variables from the first existing ``.env`` file."""

    for candidate in ENV_FILE_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            load_dotenv(path)
            break


@lru_cache(maxsize=1)
def get_config() -> ServerSettings:
    """Return cached server configuration built from environment variables."""

    load_environment()
    return ServerSettings()


def get_server_url() -> str:
    """Return the full HTTP URL for the MCP server based on configuration."""

    cfg = get_config()
    path = cfg.path if cfg.path.startswith("/") else f"/{cfg.path}"
    if not path.endswith("/"):
        path = f"{path}/"
    return f"http://{cfg.host}:{cfg.port}{path}"


def get_emplifi_credentials() -> tuple[str | None, str | None]:
    """Get Emplifi API credentials from configuration."""
    config = get_config()
    return config.emplifi_token, config.emplifi_secret


def get_emplifi_settings() -> tuple[str, int]:
    """Get Emplifi API settings from configuration."""
    config = get_config()
    return config.emplifi_api_base, config.emplifi_timeout


def get_openai_api_key() -> str | None:
    """Get OpenAI API key from configuration."""
    config = get_config()
    return config.openai_api_key


__all__ = [
    "ServerSettings",
    "get_config",
    "get_server_url",
    "load_environment",
    "get_emplifi_credentials",
    "get_emplifi_settings",
    "get_openai_api_key",
]
