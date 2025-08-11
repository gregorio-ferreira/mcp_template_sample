"""Data processing tools (template)."""

from __future__ import annotations

import json
from typing import Annotated, Any


def parse_json(
    text: Annotated[str, "JSON string to parse"],
) -> dict[str, Any]:
    """Parse JSON string to dict."""
    return json.loads(text)


def format_json(
    data: Annotated[dict[str, Any], "Mapping to serialize"],
    indent: Annotated[int | None, "Indent level"] = 2,
) -> str:
    """Serialize mapping to JSON string."""
    return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
