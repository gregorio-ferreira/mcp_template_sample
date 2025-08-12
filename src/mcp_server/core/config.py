"""Core configuration utilities for the MCP server."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE_CANDIDATES = [".env", ".env.local"]


class ServerSettings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="MCP_", case_sensitive=False)


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


__all__ = ["ServerSettings", "get_config", "get_server_url", "load_environment"]
