"""Top-level entrypoint for the packaged DVRS desktop app."""

from __future__ import annotations

from dvrs_tool.desktop import main


if __name__ == "__main__":
    raise SystemExit(main())
