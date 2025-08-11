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
- examples — Example clients for using the server
- scripts — Utility scripts (e.g. `run_server.py`)
- pyproject.toml — Project metadata, dependencies, and tool configs
- `.github/copilot-instructions.md` — This file

## Build, Run, and Test

- **Install dependencies:**  
  ```bash
  uv pip install -e .
  uv pip install -e ".[dev]"
  ```
- **Run the server:**  
  ```bash
  python scripts/run_server.py
  # or
  python -m mcp_server.server
  # or
  mcp-server
  ```
- **Run tests:**  
  ```bash
  pytest
  pytest tests/test_tools/test_time_tools.py
  ```
- **Lint & format:**  
  ```bash
  black src/ tests/
  ruff format src/ tests/
  ruff check src/ tests/
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