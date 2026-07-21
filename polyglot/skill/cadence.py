#!/usr/bin/env python3
"""Compatibility command for Polyglot's unified ambient cadence."""

from __future__ import annotations

import argparse

from polyglot.storage import load_config, save_config


def _show(config: dict) -> None:
    cadence = int(config.get("ambient_cadence", 5) or 5)
    enabled = "enabled" if config.get("ambient_enabled", False) else "disabled"
    print(f"Ambient mode: {enabled}")
    print(f"Cadence: every {cadence} completed agent turn{'s' if cadence != 1 else ''}")
    print("Set with: polyglot ambient enable --cadence 10")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="polyglot.skill.cadence",
        description="Set Polyglot's ambient phrase cadence.",
    )
    parser.add_argument("value", type=int, nargs="?")
    parser.add_argument("--codex", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--both", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    config = load_config()
    if args.value is not None:
        if args.value < 1:
            parser.error("cadence must be at least 1")
        config["ambient_cadence"] = args.value
        save_config(config)
    _show(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
