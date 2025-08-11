"""Validation script for server tools and configuration."""
from __future__ import annotations

import json

from mcp_server.server import create_server


def main() -> None:
    server = create_server("Validation")
    tool_registry = getattr(server, "_tool_registry", {})
    summary = {
        "tool_count": len(tool_registry),
        "tools": sorted(tool_registry.keys()),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
