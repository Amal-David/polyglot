#!/usr/bin/env python3
"""Legacy hook wrapper; new installs use the plugin's shared Stop hook."""

from __future__ import annotations

from polyglot.ambient import main as ambient_main


def main() -> int:
    """Run the old entry point against the new opt-in event protocol."""
    return ambient_main(["--hook", "--host", "claude"])


if __name__ == "__main__":
    raise SystemExit(main())
