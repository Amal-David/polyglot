#!/usr/bin/env python3
"""Deprecated compatibility wrapper; manifests use ``scripts/ambient.py``."""

from __future__ import annotations

import warnings

from polyglot.ambient import main as ambient_main


def main() -> int:
    """Run the compatibility entry point for existing installations only."""
    warnings.warn(
        "polyglot.skill.hook is deprecated; use the bundled scripts/ambient.py wrapper",
        DeprecationWarning,
        stacklevel=2,
    )
    return ambient_main(["--hook", "--host", "claude"])


if __name__ == "__main__":
    raise SystemExit(main())
