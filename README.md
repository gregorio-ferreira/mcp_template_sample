# MCP Server Template

A reusable Python template for building Model Context Protocol (MCP) servers using FastMCP with HTTP transport.

## Features

- 🚀 FastMCP Integration: Built on FastMCP for automatic schema generation
- 🔧 Type Safety: Full Pydantic models and Python 3.13 typing
- 🧪 Comprehensive Testing: Pytest suite with async support
- 📦 UV Package Management: Modern Python dependency management
- 🔍 Best Practices: Follows Python and MCP standards
- 🎯 Production Ready: Logging, configuration, error handling

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager

### Installation

1. Clone this template:
```bash
git clone <your-repo-url>
cd mcp-server-template
```

2. Install dependencies with UV:
```bash
uv pip install -e .
uv pip install -e ".[dev]"  # For development
```

3. Copy environment configuration:
```bash
cp .env.example .env
```

### Running the Server

```bash
# Using the script
python scripts/run_server.py

# Or directly
python -m mcp_server.server

# Or via entry point
mcp-server
```

The server will start on `http://127.0.0.1:8000/mcp/`

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file (example)
pytest tests/test_tools/test_time_tools.py

# Test MCP server functionality
make test-server          # Test with curl
make test-client          # Test with Python client
make check-server         # Check if server is running

# Interactive testing
make chat                 # Start chat agent (requires OpenAI API key)
```

### Using with LangChain/LangGraph

```bash
# Install agent dependencies
uv pip install -e ".[agent]"

# Set up your OpenAI API key in .env file
echo "OPENAI_API_KEY=your-key-here" >> .env

# Run example agent
python examples/agent_client.py

# Run interactive chat agent
python tests/test_examples/mcp_chat_agent.py
```

## Development

### Adding New Tools

1. Create a new module inside `src/mcp_server/tools/` (e.g. `my_tools.py`):
```python
# src/mcp_server/tools/my_tools.py
from typing import Annotated

def my_new_tool(
    param: Annotated[str, "Parameter description"],
) -> str:
    """Tool description."""
    return f"Echo: {param}"
```

2. (Optional) Re-export in `src/mcp_server/tools/__init__.py` so it becomes available via `from mcp_server.tools import my_new_tool`:
```python
from .my_tools import my_new_tool  # noqa: F401
```

3. Register in `src/mcp_server/server.py`:
```python
from mcp_server.tools import my_new_tool

def register_tools() -> None:
    # ... existing registrations
    mcp.tool()(my_new_tool)
```

4. Add a test file in `tests/test_tools/test_my_tools.py` covering happy path + edge cases.

### Type Checking

```bash
mypy src/
```

### Linting and Formatting

```bash
# Format code
black src/ tests/
ruff format src/ tests/

# Lint
ruff check src/ tests/
```

## Project Structure

```
├── src/mcp_server/        # Main package
│   ├── server.py          # Server implementation & tool registration
│   ├── tools/             # Tool category modules (time_tools, file_tools, etc.)
│   │   ├── __init__.py    # Re-exports selected tools
│   │   ├── time_tools.py  # Time-related tools
│   │   ├── file_tools.py  # (Template) File utilities
│   │   └── data_tools.py  # (Template) Data processing
│   ├── models.py          # Pydantic models
│   ├── config.py          # Configuration
│   └── utils.py           # Utilities
├── tests/                 # Test suite (per-tool modules under test_tools/)
│   └── test_examples/     # Integration test scripts
│       ├── test_mcp_server.sh      # Bash/curl testing
│       ├── test_mcp_client.py      # Python client testing
│       └── mcp_chat_agent.py       # Interactive AI agent
├── examples/              # Usage examples
│   ├── simple_client.py   # Basic client example
│   └── agent_client.py    # AI agent example
└── scripts/               # Utility scripts
```

## Configuration

Configure via environment variables or `.env` file:

- `MCP_HOST`: Server host (default: 127.0.0.1)
- `MCP_PORT`: Server port (default: 8000)
- `MCP_PATH`: MCP endpoint path (default: /mcp)
- `MCP_DEBUG`: Enable debug mode (default: false)
- `MCP_LOG_LEVEL`: Logging level (default: INFO)
- `OPENAI_API_KEY`: OpenAI API key for agent examples (optional)

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linting
6. Submit a pull request
