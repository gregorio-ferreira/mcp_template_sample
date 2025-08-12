"""MCP Server implementation using FastMCP."""

from __future__ import annotations

import structlog
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

from mcp_server.core import configure_logging, get_config
from mcp_server.tools import (
    convert_timezone,
    format_json,
    list_directory,
    parse_json,
    read_file,
    to_unix_time,
)

logger = structlog.get_logger(__name__)

# Singleton FastMCP instance
app_name = "MCP Server Template"
mcp = FastMCP(app_name)


def register_tools() -> None:
    """Register all tool functions with the MCP server.

    Tools accept Pydantic input models or primitive types for validation.
    Idempotent: calling multiple times won't duplicate registrations due to
    FastMCP's internal handling (safe in test setups).
    """
    registered_before = {t.name for t in getattr(mcp, "tools", [])}
    # Core tools
    mcp.tool()(convert_timezone)
    mcp.tool()(to_unix_time)
    # File tools
    mcp.tool()(read_file)
    mcp.tool()(list_directory)
    # Data tools
    mcp.tool()(parse_json)
    mcp.tool()(format_json)
    registered_after = {t.name for t in getattr(mcp, "tools", [])}
    added = registered_after - registered_before
    if added:
        logger.info("Registered tools: %s", ", ".join(sorted(added)))


def main() -> None:
    """Main entry point for the server."""
    config = get_config()
    configure_logging(config.log_level)
    logger.info("Starting MCP server on %s:%s%s", config.host, config.port, config.path)
    register_tools()
    # Serve HTTP using configuration values (overridable via environment variables)
    # You can override host/port/path via CLI as well:
    #   fastmcp run src/mcp_server/server.py --transport http --port 9000
    mcp.run(
        transport="http",
        host=config.host,
        port=config.port,
        path=config.path,
        stateless_http=True,
    )


if __name__ == "__main__":  # pragma: no cover
    # Wrap the MCP ASGI app with CORS middleware for browser support
    base_app = mcp.http_app()
    cors_app = CORSMiddleware(
        base_app,
        # Dev: allow all origins (tighten in production)
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    import uvicorn

    uvicorn.run(cors_app, host="0.0.0.0", port=8000)
