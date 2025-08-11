"""Main MCP server implementation using FastMCP."""
from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from mcp_server.config import get_config
from mcp_server.utils import setup_logging
from mcp_server.tools import convert_timezone, to_unix_time

logger = logging.getLogger(__name__)

# Singleton FastMCP instance
mcp = FastMCP("MCP Server Template")


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
    logger.info(
        "Starting MCP server on %s:%s%s", config.host, config.port, config.path
    )
    register_tools()
    mcp.run(
        transport="http",
        host=config.host,
        port=config.port,
        path=config.path,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
