"""Server structure tests using singleton registration pattern."""

import anyio
import pytest

from mcp_server.core import get_config
from mcp_server.server import main, mcp, register_tools


class TestServerStructure:
    """Test server structure and compliance."""

    def test_server_singleton(self) -> None:
        register_tools()
        assert mcp is not None

    def test_tool_registration_count(self) -> None:
        register_tools()
        tools = anyio.run(mcp.get_tools)
        expected_tools = {
            "list_listening_queries",
            "fetch_listening_posts",
            "get_recent_posts"
        }
        assert expected_tools.issubset(tools.keys())


def test_environment_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should drive server configuration."""

    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9001")
    monkeypatch.setenv("MCP_PATH", "/custom")
    get_config.cache_clear()

    captured: dict[str, object] = {}

    def fake_run(
        *,
        transport: str,
        host: str,
        port: int,
        path: str,
        stateless_http: bool,
    ) -> None:
        del transport, stateless_http
        captured.update(host=host, port=port, path=path)

    monkeypatch.setattr("mcp_server.server.mcp.run", fake_run)
    main()

    assert captured == {"host": "0.0.0.0", "port": 9001, "path": "/custom"}
