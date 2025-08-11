"""Server structure tests using singleton registration pattern."""
from __future__ import annotations

import pytest

from mcp_server.server import mcp, register_tools


class TestServerStructure:
    """Test server structure and compliance."""

    def test_server_singleton(self) -> None:
        register_tools()
        assert mcp is not None

    @pytest.mark.asyncio
    async def test_tool_registration_count(self) -> None:
        register_tools()
        # list_tools is async; ensure core tools present
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert {"convert_timezone", "to_unix_time"}.issubset(names)
