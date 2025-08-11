"""File operation tools for the MCP server."""

from pathlib import Path
from typing import Annotated


def read_file(
    path: Annotated[str, "Path to the file to read"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
) -> str:
    """Return contents of file at path."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    if not p.is_file():
        raise ValueError(f"Not a file: {path}")
    return p.read_text(encoding=encoding)


def list_directory(
    path: Annotated[str, "Directory to list"],
) -> list[str]:
    """Return file names in directory (non-recursive)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    if not p.is_dir():
        raise NotADirectoryError(path)
    return [str(child) for child in p.iterdir() if child.is_file()]
