"""Run the MCP server."""

from mcp_server.core import get_config
from mcp_server.server import main

if __name__ == "__main__":  # pragma: no cover
    cfg = get_config()
    print(f"Starting MCP server on http://{cfg.host}:{cfg.port}{cfg.path}")
    main()
