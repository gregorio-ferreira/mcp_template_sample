"""Server structure tests using singleton registration pattern."""

from pathlib import Path

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
        expected_tools = {"list_listening_queries", "fetch_listening_posts", "get_recent_posts"}
        assert expected_tools.issubset(tools.keys())


def test_environment_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Configuration should load values from an ``.env`` file."""

    env_file = tmp_path / ".env"
    env_file.write_text(
        "MCP_HOST=0.0.0.0\nMCP_PORT=9001\nMCP_PATH=/custom\n",
    )
    monkeypatch.setattr(
        "mcp_server.core.config.ENV_FILE_CANDIDATES",
        [str(env_file)],
    )
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
