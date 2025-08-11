"""Simple client example showing direct tool usage (no agent)."""
from __future__ import annotations

from mcp_server.tools import convert_timezone, to_unix_time


def main() -> None:
    print(
        "Convert Europe/Madrid -> America/New_York:",
        convert_timezone("2025-08-10 09:30", "Europe/Madrid", "America/New_York"),
    )
    print(
        "Unix time (ms):",
        to_unix_time("2025-08-10T09:30:00+02:00", unit="milliseconds"),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
