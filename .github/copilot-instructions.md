## Project Overview

This repository is a Python template for building Model Context Protocol (MCP) servers using FastMCP. It provides a modular structure for defining, testing, and exposing tools (functions) via an HTTP API, with type safety (Pydantic), modern Python (3.13+), and best practices for testing, linting, and packaging.

## Layout & Key Files

- mcp_server — Main package
  - server.py — Entry point, registers tools, runs FastMCP server
  - `tools/` — All tool modules (e.g. time_tools.py, `file_tools.py`, `data_tools.py`)
  - __init__.py — Re-exports selected tools for easy import
  - models.py — Pydantic models for input/output validation
  - `config.py`, `utils.py` — Configuration and utility helpers
- tests — Pytest suite, with per-tool test modules under `test_tools/`
  - `test_examples/` — Integration test scripts (bash, Python client, AI agent)
- examples — Example clients for using the server (simple client, AI agent)
- scripts — Utility scripts (e.g. `run_server.py`)
- pyproject.toml — Project metadata, dependencies, and tool configs
- `.env` — Environment variables (copy from `.env.example`)
- `Makefile` — Development workflow commands
- `.github/copilot-instructions.md` — This file

## Build, Run, and Test

- **Install dependencies:**  
  ```bash
  uv sync
  uv pip install -e ".[dev]"      # Development dependencies
  uv pip install -e ".[agent]"    # AI agent dependencies (optional)
  ```
- **Run the server:**  
  ```bash
  make run
  # or
  python scripts/run_server.py
  # or
  python -m mcp_server.server
  # or
  mcp-server
  ```
- **Run tests:**  
  ```bash
  make test              # Unit tests
  make test-server       # Integration test with curl
  make test-client       # Integration test with Python client
  make check-server      # Check if server is running
  ```
- **Run examples:**
  ```bash
  make example           # Simple client example
  make agent             # AI agent example (requires OpenAI API key)
  make chat              # Interactive chat agent
  ```
- **Lint & format:**  
  ```bash
  make format            # Format code
  make lint              # Lint code
  make mypy              # Type checking
  ```

## Coding Standards

- Use Python 3.13+ features and type hints.
- Organize tools as functions in tools modules.
- Register tools in server.py using `mcp.tool()(function)`.
- Use Pydantic models for input/output validation.
- Write tests for each tool in test_tools.

## Best Practices

- Do not use or reference the deprecated tools.py file.
- Only add new tools as modules under tools.
- Re-export tools in __init__.py for easy import.
- Keep coverage and test artifacts out of version control (see .gitignore).
- Follow the structure and examples in the README for adding new tools and tests.

## Additional Notes

- The template is designed for easy extension: add new tool modules, register them in server.py, and add tests.
- All configuration, linting, and formatting settings are in pyproject.toml.
- The server exposes tools via HTTP using FastMCP; see README.md for usage and agent integration.

---

This file will guide Copilot to work efficiently with your codebase, minimizing exploration and errors. If you want more granular instructions (e.g. per-directory), you can use `.github/instructions/*.instructions.md` files with `applyTo` frontmatter as described in the [docs](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions).