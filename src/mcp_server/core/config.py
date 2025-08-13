"""Core configuration utilities for the MCP server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_CANDIDATES = [".env", ".env.local"]


class ServerSettings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    # MCP Server settings
    host: str = Field(default="127.0.0.1", alias="MCP_HOST")
    port: int = Field(default=8000, alias="MCP_PORT")
    path: str = Field(default="/mcp", alias="MCP_PATH")
    debug: bool = Field(default=False, alias="MCP_DEBUG")
    log_level: str = Field(default="INFO", alias="MCP_LOG_LEVEL")

    # Emplifi API credentials
    emplifi_token: str | None = Field(default=None, alias="EMPLIFI_TOKEN")
    emplifi_secret: str | None = Field(default=None, alias="EMPLIFI_SECRET")
    emplifi_api_base: str = Field(default="https://api.emplifi.io/3", alias="EMPLIFI_API_BASE")
    emplifi_timeout: int = Field(default=30, alias="EMPLIFI_TIMEOUT")

    # OpenAI API credentials (for AI-powered chat agent)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


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
