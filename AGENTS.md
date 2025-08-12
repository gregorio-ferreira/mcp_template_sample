# MCP Server Template - Agent Gui└── test_examples/      # Integration testing scripts & examples
    ├── test_mcp_server.sh      # Raw curl/bash testing
    ├── test_mcp_client.py      # Python client testing  
    └── mcp_chat_agent.py       # Interactive AI agent repository is a Python template for building Model Context Protocol (MCP) servers using FastMCP. This guide helps AI agents understand how to work effectively within this codebase.

## Project Overview

**What this is:** A production-ready template for creating MCP servers that expose tools via HTTP API, with full LangChain/LangGraph integration for AI agents.

**Key Technologies:**
- FastMCP 2.11+ for MCP server implementation
- Python 3.13+ with modern typing and Pydantic validation
- UV for package management and execution
- LangChain/LangGraph for AI agent integration
- OpenAI GPT-4o-mini for conversational capabilities

## Repository Structure & Navigation

### Core Directories
```
src/mcp_server/           # Main package - focus here for server logic
├── core/               # Configuration and logging utilities
│   ├── config.py       # Server configuration
│   └── logging.py      # Logging setup
├── server.py          # Tool registration & FastMCP server setup
├── tools/             # Tool implementations (add new tools here)
│   ├── time_tools.py  # Working example: timezone & time tools
│   ├── file_tools.py  # Template for file operations
│   └── data_tools.py  # Template for data processing
├── models.py          # Pydantic models for validation
└── utils.py           # Shared utilities

tests/                   # Test suite
├── test_tools/         # Unit tests per tool module
└── test_examples/      # Integration testing scripts
    ├── test_mcp_server.sh     # Bash/curl testing
    ├── test_mcp_client.py     # Python client testing  
    └── mcp_chat_agent.py      # Interactive AI agent

examples/               # Usage examples
├── simple_client.py   # Basic FastMCP client
└── agent_client.py    # AI agent with LangChain
```

The `core` package centralizes configuration loading and logging helpers used by
the server, tests, and example scripts.

### Important Files
- `pyproject.toml` - Dependencies, build config, tool settings
- `Makefile` - Development workflow commands
- `.env` - Environment configuration (copy from `.env.example`)
- `scripts/run_server.py` - Server entry point

## Development Environment

### Quick Setup
```bash
# 1. Install dependencies
make setup

# 2. Configure environment (set OPENAI_API_KEY for agents)
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start the server
make run

# 4. Test everything works
make check-server
```

### Essential Commands
```bash
# Development
make run              # Start MCP server
make setup            # Install deps + setup .env
make clean            # Clean cache files

# Code Quality  
make format           # Format with Ruff
make lint             # Lint with Ruff  
make mypy             # Type checking
make test             # Unit tests

# Testing & Validation
make test-server      # Test with curl/bash
make test-client      # Test with Python client
make check-server     # Quick server status check

# Examples & Agents
make example          # Run simple client example
make agent            # Run AI agent example  
make chat             # Interactive conversational agent
```

## Working with Tools

### Adding New Tools
1. **Create tool module** in `src/mcp_server/tools/my_tools.py`:
```python
from typing import Annotated

def my_tool(
    param: Annotated[str, "Parameter description"],
) -> str:
    """Tool description for the agent."""
    return f"Result: {param}"
```

2. **Register in server** (`src/mcp_server/server.py`):
```python
from mcp_server.tools import my_tool

def register_tools() -> None:
    # ... existing tools
    mcp.tool()(my_tool)
```

3. **Add tests** in `tests/test_tools/test_my_tools.py`
4. **Re-export** in `src/mcp_server/tools/__init__.py` (optional)

### Tool Best Practices
- Use type hints and `Annotated` for parameter descriptions
- Write comprehensive docstrings (agents read these)
- Handle errors gracefully with try/catch
- Validate inputs with Pydantic when complex
- Test both happy path and edge cases

## Testing & Validation

### Validation Workflow
```bash
# 1. Start server in one terminal
make run

# 2. Run full test suite in another terminal
make test              # Unit tests
make test-server       # Integration tests (curl)
make test-client       # Integration tests (Python)
make check-server      # Server health check
```

### Test Structure
- **Unit tests:** `tests/test_tools/` - Test individual tools
- **Integration tests:** `tests/test_examples/` - End-to-end testing and examples

### Before Committing
```bash
make format           # Auto-format code
make lint             # Check code quality  
make mypy             # Type checking
make test             # Run all tests
make clean            # Clean artifacts
```

## AI Agent Integration

### Available Agents
1. **Client Testing** (`tests/test_examples/test_mcp_client.py`) - Comprehensive tool testing
2. **Chat Agent** (`tests/test_examples/mcp_chat_agent.py`) - Interactive AI conversations
3. **Server Testing** (`tests/test_examples/test_mcp_server.sh`) - Raw curl/bash validation

### Agent Dependencies
```bash
# Install agent dependencies
uv pip install -e ".[agent]"

# Required environment variables
OPENAI_API_KEY=your-api-key-here  # In .env file
```

### Agent Architecture
- **MCP Server** provides tools via HTTP
- **LangChain MCP Adapters** bridge MCP ↔ LangChain
- **LangGraph** handles conversation flow and memory
- **OpenAI GPT-4o-mini** powers natural language understanding

## Environment Configuration

### Required Environment Variables
```bash
# Server Configuration
MCP_HOST=127.0.0.1           # Server host
MCP_PORT=8000                # Server port  
MCP_PATH=/mcp                # MCP endpoint path
MCP_DEBUG=false              # Debug mode
MCP_LOG_LEVEL=INFO           # Logging level

# AI Agent Configuration (optional)
OPENAI_API_KEY=sk-xxx        # OpenAI API key for agents
```

### Package Management
- Use `uv` for all Python package operations
- Dependencies defined in `pyproject.toml`
- Optional dependencies: `[dev]`, `[agent]`
- Lock file: `uv.lock`

## Code Style & Standards

### Python Standards
- Python 3.13+ features and syntax
- Type hints everywhere (`from __future__ import annotations`)
- Pydantic models for data validation
- Modern async/await patterns
- Docstrings for all public functions

### Code Quality Tools
- **Ruff:** Formatting and linting (replaces Black + Flake8)
- **MyPy:** Static type checking
- **Pytest:** Testing with async support
- Line length: 100 characters (configured in `pyproject.toml`)

### File Organization
- Tools in separate modules by category
- One tool per function (not classes)
- Clear separation of concerns
- Import from `mcp_server.tools` for registered tools

## Common Tasks for Agents

### Adding a New Tool Category
1. Create `src/mcp_server/tools/category_tools.py`
2. Implement tools with proper typing and docs
3. Add to `src/mcp_server/tools/__init__.py` exports
4. Register tools in `src/mcp_server/server.py`
5. Create `tests/test_tools/test_category_tools.py`
6. Test with `make test-server` and `make test-client`

### Debugging Issues
1. Check server logs: `make run` (shows FastMCP output)
2. Test server health: `make check-server`
3. Test specific tools: `make test-client`
4. Check environment: verify `.env` file and dependencies

### Working with Existing Code
- **Time tools** (`time_tools.py`) - Complete working example
- **File/Data tools** - Templates to implement
- **Server setup** (`server.py`) - Tool registration patterns
- **Test examples** - Integration testing patterns

## Agent-Specific Instructions

### When Adding Features
1. **Read existing code** in `src/mcp_server/tools/time_tools.py` for patterns
2. **Follow the same structure** for new tools
3. **Test thoroughly** with both unit tests and integration tests
4. **Update documentation** if adding major features

### When Debugging
1. **Check server status** with `make check-server` first
2. **Look at logs** from `make run` for detailed errors
3. **Test step-by-step** using the test scripts
4. **Verify environment** setup and dependencies

### When Refactoring
1. **Run tests first** to establish baseline: `make test`
2. **Make incremental changes** and test after each step
3. **Maintain backwards compatibility** for existing tools
4. **Update tests** to match any API changes

## Error Handling Patterns

### Tool Error Handling
```python
def robust_tool(param: str) -> str:
    """Tool with proper error handling."""
    try:
        # Tool logic here
        return f"Success: {param}"
    except ValueError as e:
        raise ValueError(f"Invalid input: {e}")
    except Exception as e:
        raise RuntimeError(f"Tool failed: {e}")
```

### Testing Error Cases
```python
def test_tool_error_handling():
    with pytest.raises(ValueError, match="Invalid input"):
        robust_tool("invalid_input")
```

This guide should help you work effectively within this MCP server template. Focus on the `src/mcp_server/tools/` directory for most development work, and use the testing infrastructure to validate changes.
