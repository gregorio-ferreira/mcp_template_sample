"""MCP Server implementation using FastMCP."""

import logging

from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from mcp_server.config import get_config
from mcp_server.utils import setup_logging
from mcp_server.tools import convert_timezone, to_unix_time

logger = logging.getLogger(__name__)

# Singleton FastMCP instance
app_name = "MCP Server Template"
mcp = FastMCP(app_name)


def register_tools() -> None:
    """Register all tool functions with the MCP server.

    Idempotent: calling multiple times won't duplicate registrations due to
    FastMCP's internal handling (safe in test setups).
    """
    registered_before = {t.name for t in getattr(mcp, "tools", [])}
    # Core tools
    mcp.tool()(convert_timezone)
    mcp.tool()(to_unix_time)
    registered_after = {t.name for t in getattr(mcp, "tools", [])}
    added = registered_after - registered_before
    if added:
        logger.info("Registered tools: %s", ", ".join(sorted(added)))


def main() -> None:
    """Main entry point for the server."""
    config = get_config()
    setup_logging(config.log_level)
    logger.info("Starting MCP server on %s:%s%s", config.host, config.port, config.path)
    register_tools()
    # Serve HTTP on localhost:8000 at path /mcp (recommended for web deployments)
    # You can override host/port/path via CLI: fastmcp run src/mcp_server/server.py --transport http --port 9000
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp",
        stateless_http=True,
    )


if __name__ == "__main__":  # pragma: no cover
    # Wrap the MCP ASGI app with CORS middleware for browser support
    app = mcp.http_app()
    app = CORSMiddleware(
        app,
        # Dev: allow all origins (tighten in production)
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
