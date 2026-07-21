"""Command-line interface for browsing, sampling, and ambient configuration."""

from __future__ import annotations

import argparse
import json
from typing import Any

from polyglot import __version__
from polyglot.ambient import format_companion_message, sample_phrase
from polyglot.data.content_loader import ALL_PAIRS, get_pair
from polyglot.skill.config import load_hook_state
from polyglot.storage import (
    get_active_pair_id,
    load_config,
    save_config,
    set_active_pair_id,
)


def _pair_or_error(parser: argparse.ArgumentParser, pair_id: str):
    pair = get_pair(pair_id)
    if pair is None:
        parser.error(f"unknown language pair: {pair_id}")
    return pair


def _status_payload() -> dict[str, Any]:
    config = load_config()
    state = load_hook_state()
    counts = state.get("host_turn_counts")
    return {
        "enabled": bool(config.get("ambient_enabled", False)),
        "active_pair": config.get("active_pair_id"),
        "cadence": int(config.get("ambient_cadence", 5) or 5),
        "host_turn_counts": counts if isinstance(counts, dict) else {},
    }


def _configure_ambient(
    parser: argparse.ArgumentParser,
    action: str,
    *,
    pair_id: str | None,
    cadence: int | None,
) -> dict[str, Any]:
    config = load_config()
    if pair_id:
        _pair_or_error(parser, pair_id)
        set_active_pair_id(pair_id)
        config = load_config()
    if cadence is not None:
        if cadence < 1:
            parser.error("cadence must be at least 1")
        config["ambient_cadence"] = cadence

    if action == "enable":
        if not config.get("active_pair_id"):
            parser.error("select a pair with --pair or `polyglot pair PAIR_ID` first")
        config["ambient_enabled"] = True
    elif action == "disable":
        config["ambient_enabled"] = False

    save_config(config)
    return _status_payload()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyglot",
        description="Learn one phrase at a time across 70 language pairs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("browse", help="Open the interactive language-pair cabinet.")

    phrase = sub.add_parser("sample", aliases=["phrase"], help="Show one phrase now.")
    phrase.add_argument("--pair", help="Pair id, such as en-es; defaults to the active pair.")
    phrase.add_argument("--json", action="store_true", help="Emit the phrase as JSON.")

    pairs = sub.add_parser("pairs", help="List all available language pairs.")
    pairs.add_argument("--json", action="store_true", help="Emit the pair catalog as JSON.")

    pair = sub.add_parser("pair", help="Show or set the active language pair.")
    pair.add_argument("pair_id", nargs="?", help="Pair id to activate, such as en-ja.")
    pair.add_argument("--json", action="store_true", help="Emit the result as JSON.")

    ambient = sub.add_parser("ambient", help="Configure optional agent-turn phrases.")
    ambient.add_argument(
        "action",
        nargs="?",
        choices=("enable", "disable", "status"),
        default="status",
    )
    ambient.add_argument("--pair", help="Select a pair while enabling ambient mode.")
    ambient.add_argument("--cadence", type=int, help="Show a phrase every N completed turns.")
    ambient.add_argument("--json", action="store_true", help="Emit status as JSON.")
    return parser


def _print_status(payload: dict[str, Any]) -> None:
    enabled = "enabled" if payload["enabled"] else "disabled"
    pair_id = payload["active_pair"] or "(none)"
    print(f"Ambient mode: {enabled}")
    print(f"Active pair:  {pair_id}")
    print(f"Cadence:      every {payload['cadence']} completed turns")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = args.command or "browse"

    if command == "browse":
        from polyglot.app import run

        run()
        return 0

    if command in {"sample", "phrase"}:
        pair_id = args.pair or get_active_pair_id()
        if not pair_id:
            parser.error("select a pair with --pair or `polyglot pair PAIR_ID` first")
        _pair_or_error(parser, pair_id)
        phrase = sample_phrase(pair_id)
        if phrase is None:
            return 1
        if args.json:
            print(json.dumps(phrase, ensure_ascii=False))
        else:
            print(format_companion_message(phrase))
        return 0

    if command == "pairs":
        pairs = [
            {
                "id": pair.id,
                "source": pair.source_lang,
                "target": pair.target_lang,
                "native_name": pair.target_native,
                "entries": len(pair.phrases),
            }
            for pair in ALL_PAIRS
        ]
        if args.json:
            print(json.dumps(pairs, ensure_ascii=False))
        else:
            for pair in pairs:
                print(
                    f"{pair['id']:<7} {pair['source']} → {pair['target']} "
                    f"({pair['native_name']}) — {pair['entries']} entries"
                )
        return 0

    if command == "pair":
        if args.pair_id:
            pair = _pair_or_error(parser, args.pair_id)
            set_active_pair_id(pair.id)
        active_pair = get_active_pair_id()
        payload = {"active_pair": active_pair}
        if args.json:
            print(json.dumps(payload))
        else:
            print(active_pair or "(no active pair)")
        return 0

    if command == "ambient":
        if args.action == "status":
            if args.pair is not None or args.cadence is not None:
                parser.error("--pair and --cadence require `ambient enable`")
            payload = _status_payload()
        else:
            payload = _configure_ambient(
                parser,
                args.action,
                pair_id=args.pair,
                cadence=args.cadence,
            )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            _print_status(payload)
        return 0

    parser.error(f"unknown command: {command}")
    return 2
