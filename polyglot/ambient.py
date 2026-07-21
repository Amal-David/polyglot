"""Host-neutral ambient phrase delivery."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from polyglot.data.content_loader import get_pair
from polyglot.skill.config import (
    get_active_pair_id,
    get_ambient_cadence,
    get_ambient_enabled,
    load_hook_state,
    save_hook_state,
)
from polyglot.storage import load_config, save_config, set_active_pair_id
from polyglot.skill.phrase_picker import (
    format_phrase_message,
    pick_phrase,
    total_phrase_count,
)

VALID_HOSTS = {"claude", "codex", "hermes", "pi"}


def detect_hook_host() -> str:
    """Identify Codex's compatibility environment, falling back to Claude."""
    return "codex" if os.environ.get("PLUGIN_ROOT") else "claude"


def format_companion_message(phrase: dict[str, Any]) -> str:
    """Format a compact phrase card for agent and terminal surfaces."""
    return format_phrase_message(
        phrase,
        total_phrase_count(phrase["pair_id"]),
        phrase["pair_label"],
    )


def next_ambient_message(host: str) -> str | None:
    """Return a phrase when ambient mode and this host's cadence allow it."""
    if host not in VALID_HOSTS:
        raise ValueError(f"unsupported host: {host}")
    if not get_ambient_enabled():
        return None

    pair_id = get_active_pair_id()
    if not pair_id:
        return None

    state = load_hook_state()
    counts = state.get("host_turn_counts")
    if not isinstance(counts, dict):
        counts = {}
    turn_count = int(counts.get(host, 0) or 0) + 1
    counts[host] = turn_count
    state["host_turn_counts"] = counts
    save_hook_state(state)

    cadence = get_ambient_cadence()
    if turn_count % cadence != 0:
        return None

    phrase = pick_phrase(pair_id)
    return format_companion_message(phrase) if phrase else None


def sample_phrase(pair_id: str | None = None) -> dict[str, Any] | None:
    """Sample immediately, bypassing ambient enablement and cadence."""
    return pick_phrase(pair_id)


def configure(
    *,
    enabled: bool | None = None,
    pair_id: str | None = None,
    cadence: int | None = None,
) -> dict[str, Any]:
    """Update portable Polyglot state without touching any host configuration."""
    changed = False
    if pair_id is not None:
        if get_pair(pair_id) is None:
            raise ValueError(f"unknown language pair: {pair_id}")
        set_active_pair_id(pair_id)
        changed = True
    config = load_config()
    if cadence is not None:
        if cadence < 1:
            raise ValueError("cadence must be at least 1")
        config["ambient_cadence"] = cadence
        changed = True
    if enabled is not None:
        if enabled and not config.get("active_pair_id"):
            raise ValueError("select a pair before enabling ambient mode")
        config["ambient_enabled"] = enabled
        changed = True
    if changed:
        save_config(config)
    return {
        "enabled": bool(config.get("ambient_enabled", False)),
        "active_pair": config.get("active_pair_id"),
        "cadence": int(config.get("ambient_cadence", 5) or 5),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit a Polyglot phrase safely.")
    parser.add_argument(
        "--host",
        choices=("auto", *sorted(VALID_HOSTS)),
        default="auto",
        help="Agent host for cadence accounting.",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--hook", action="store_true", help="Emit hook-protocol JSON.")
    action.add_argument("--sample", action="store_true", help="Bypass ambient cadence.")
    action.add_argument("--enable", action="store_true", help="Enable ambient mode.")
    action.add_argument("--disable", action="store_true", help="Disable ambient mode.")
    action.add_argument("--status", action="store_true", help="Show ambient configuration.")
    parser.add_argument("--pair", help="Language pair id, such as en-es.")
    parser.add_argument("--cadence", type=int, help="Completed turns between phrases.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the shared script protocol without ever failing an agent turn."""
    args = _parser().parse_args(argv)
    try:
        host = detect_hook_host() if args.host == "auto" else args.host
        if args.enable or args.disable or args.status:
            payload = configure(
                enabled=True if args.enable else (False if args.disable else None),
                pair_id=args.pair,
                cadence=args.cadence,
            )
            if args.json:
                print(json.dumps(payload, ensure_ascii=False))
            else:
                state = "enabled" if payload["enabled"] else "disabled"
                print(
                    f"Polyglot ambient mode is {state}; pair "
                    f"{payload['active_pair'] or '(none)'}, cadence {payload['cadence']}."
                )
            return 0
        if args.sample:
            phrase = sample_phrase(args.pair)
            if args.json:
                print(json.dumps(phrase or {}, ensure_ascii=False))
            elif phrase:
                print(format_companion_message(phrase))
            return 0

        message = next_ambient_message(host)
        if args.hook:
            print(
                json.dumps(
                    {"systemMessage": message} if message else {},
                    ensure_ascii=False,
                )
            )
        elif args.json:
            print(json.dumps({"message": message} if message else {}, ensure_ascii=False))
        elif message:
            print(message)
    except Exception:
        if args.hook or args.json:
            print("{}")
        else:
            print("Polyglot could not complete that request.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
