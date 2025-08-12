"""Server structure tests using singleton registration pattern."""

import anyio

from mcp_server.server import mcp, register_tools


class TestServerStructure:
    """Test server structure and compliance."""

    def test_server_singleton(self) -> None:
        register_tools()
        assert mcp is not None

    def test_tool_registration_count(self) -> None:
        register_tools()
        tools = anyio.run(mcp.get_tools)
        assert {"convert_timezone", "to_unix_time"}.issubset(tools.keys())
