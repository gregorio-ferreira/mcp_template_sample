"""Validate registered tools in the MCP server.

Usage:
    uv run validate-server
    # or
    uv run python scripts/validate_server.py
"""

from __future__ import annotations

import json

import anyio

from mcp_server.server import mcp, register_tools


def main() -> None:
    """Register tools and print summary."""
    register_tools()
    tools = anyio.run(mcp.get_tools)
    names = sorted(tools.keys())
    summary = {"tool_count": len(names), "tools": names}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
