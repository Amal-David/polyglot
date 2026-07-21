"""Command-line interface for browsing, sampling, and ambient configuration."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from polyglot import __version__
from polyglot.ambient import (
    ambient_learning_status,
    format_companion_message,
    sample_phrase,
)
from polyglot.data.content_loader import ALL_PAIRS, get_pair
from polyglot.skill.config import load_hook_state
from polyglot.storage import (
    get_active_pair_id,
    learner_data_dir,
    load_config,
    save_config,
    set_active_pair_id,
    update_config,
)


def _learner_store():
    from polyglot.learning_store import LearnerStore

    store = LearnerStore(learner_data_dir())
    if store.consume_quarantine_notice():
        print("Polyglot quarantined unreadable local learner state and started fresh.", file=sys.stderr)
    return store


def _pair_or_error(parser: argparse.ArgumentParser, pair_id: str):
    pair = get_pair(pair_id)
    if pair is None:
        parser.error(f"unknown language pair: {pair_id}")
    return pair


def _status_payload() -> dict[str, Any]:
    config = load_config()
    state = load_hook_state()
    counts = state.get("host_turn_counts")
    payload = {
        "enabled": bool(config.get("ambient_enabled", False)),
        "active_pair": config.get("active_pair_id"),
        "cadence": int(config.get("ambient_cadence", 5) or 5),
        "host_turn_counts": counts if isinstance(counts, dict) else {},
    }
    payload.update(ambient_learning_status(payload["active_pair"]))
    return payload


def _configure_ambient(
    parser: argparse.ArgumentParser,
    action: str,
    *,
    pair_id: str | None,
    cadence: int | None,
) -> dict[str, Any]:
    if pair_id:
        _pair_or_error(parser, pair_id)
        set_active_pair_id(pair_id)
    if cadence is not None and cadence < 1:
        parser.error("cadence must be at least 1")

    def apply(config: dict) -> None:
        if cadence is not None:
            config["ambient_cadence"] = cadence
        if action == "enable":
            if not config.get("active_pair_id"):
                parser.error("select a pair with --pair or `polyglot pair PAIR_ID` first")
            config["ambient_enabled"] = True
        elif action == "disable":
            config["ambient_enabled"] = False

    update_config(apply)
    return _status_payload()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyglot",
        description="Learn one phrase at a time across 74 language pairs.",
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

    review = sub.add_parser("review", help="Practice due cards with typed recall.")
    review.add_argument("--pair", help="Pair id; defaults to the active pair.")
    review.add_argument("--direction", choices=("forward", "reverse", "cloze"), default="forward")
    review.add_argument("--count", type=int, default=5, help="Cards in this session (default: 5).")
    review.add_argument("--json", action="store_true", help="Preview a session without recording grades.")

    progress = sub.add_parser("progress", help="Show compact learner progress.")
    progress.add_argument("--pair", help="Limit progress to one pair.")
    progress.add_argument("--json", action="store_true", help="Emit progress as JSON.")

    goal = sub.add_parser("goal", help="Show or set a pair's daily review goal.")
    goal.add_argument("daily", nargs="?", type=int, help="Daily review goal (1–100).")
    goal.add_argument("--pair", help="Pair id; defaults to the active pair.")
    goal.add_argument("--json", action="store_true", help="Emit goal as JSON.")

    forget = sub.add_parser("forget", help="Forget learner progress, never catalog content.")
    forget_group = forget.add_mutually_exclusive_group()
    forget_group.add_argument("--pair", help="Forget one pair; defaults to the active pair.")
    forget_group.add_argument("--all", action="store_true", help="Forget all local learner progress.")
    forget.add_argument("--yes", action="store_true", help="Confirm the irreversible local action.")
    forget.add_argument("--json", action="store_true", help="Emit the result as JSON.")

    export = sub.add_parser("export", help="Write an explicit portable learner-state export.")
    export.add_argument("path", help="Destination JSON file.")
    export.add_argument("--json", action="store_true", help="Emit the result as JSON.")

    imported = sub.add_parser("import", help="Import a validated learner-state export.")
    imported.add_argument("path", help="Source JSON file.")
    imported.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    return parser


def _print_status(payload: dict[str, Any]) -> None:
    enabled = "enabled" if payload["enabled"] else "disabled"
    pair_id = payload["active_pair"] or "(none)"
    print(f"Ambient mode: {enabled}")
    print(f"Active pair:  {pair_id}")
    print(f"Cadence:      every {payload['cadence']} completed turns")
    print(f"Learning:     {payload['learning_state']}")
    print(f"Next step:    {payload['next_step']}")


def _active_learning_pair(parser: argparse.ArgumentParser, requested: str | None):
    pair_id = requested or get_active_pair_id()
    if not pair_id:
        parser.error("select a pair with --pair or `polyglot pair PAIR_ID` first")
    return _pair_or_error(parser, pair_id)


def _review_payload(cards) -> dict[str, Any]:
    return {
        "cards": [
            {
                "id": card.card_id,
                "pair_id": card.pair_id,
                "direction": card.direction,
                "prompt": card.prompt,
                "mode": card.mode,
            }
            for card in cards
        ]
    }


def _run_interactive_review(store, cards) -> int:
    for number, card in enumerate(cards, start=1):
        print(f"\n{number}/{len(cards)}  {card.prompt}")
        try:
            input("> ")  # Answers are deliberately never retained.
            input("Press Enter to reveal…")
        except (EOFError, KeyboardInterrupt):
            print("\nReview paused; this card was not graded.")
            return 0
        print(f"Answer: {card.answer}")
        if card.hint:
            print(f"Hint: {card.hint}")
        while True:
            try:
                grade = input("Grade [again/hard/good/easy]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nReview paused; this card was not graded.")
                return 0
            if grade in {"again", "hard", "good", "easy"}:
                store.record_grade(card.pair_id, card.card_id, card.direction, grade, time.time(), mode=card.mode)
                break
            print("Use again, hard, good, or easy. Nothing was recorded.")
    return 0


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
            rendered = format_companion_message(phrase)
            if not rendered:
                return 1
            print(rendered)
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

    if command == "review":
        from polyglot.review import build_review_session

        if args.count < 1 or args.count > 50:
            parser.error("--count must be between 1 and 50")
        pair = _active_learning_pair(parser, args.pair)
        cards = build_review_session(_learner_store(), pair, args.direction, time.time(), limit=args.count)
        if args.json:
            print(json.dumps(_review_payload(cards), ensure_ascii=False))
            return 0
        if not cards:
            print("No due or new cards are available for this pair.")
            return 0
        return _run_interactive_review(_learner_store(), cards)

    if command == "progress":
        if args.pair:
            _pair_or_error(parser, args.pair)
        payload = _learner_store().progress(args.pair, time.time())
        if args.pair:
            payload["pair_id"] = args.pair
            payload["goal"] = _learner_store().get_goal(args.pair)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            scope = args.pair or "all pairs"
            print(f"Progress ({scope}): {payload['due']} due · {payload['learning']} learning · {payload['reviewed_today']} today")
        return 0

    if command == "goal":
        pair = _active_learning_pair(parser, args.pair)
        store = _learner_store()
        daily = store.set_goal(pair.id, args.daily) if args.daily is not None else store.get_goal(pair.id)
        payload = {"pair_id": pair.id, "daily_goal": daily}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"Daily goal for {pair.id}: {daily} reviews")
        return 0

    if command == "forget":
        if not args.yes:
            parser.error("forget requires --yes")
        pair_id = None
        if not args.all:
            pair = _active_learning_pair(parser, args.pair)
            pair_id = pair.id
        removed = _learner_store().forget(pair_id)
        payload = {"forgotten": removed, "pair_id": pair_id}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"Forgot {removed} learner cards{' for ' + pair_id if pair_id else ''}.")
        return 0

    if command == "export":
        from polyglot.learning_store import write_export

        write_export(args.path, _learner_store().export_data())
        payload = {"path": args.path}
        print(json.dumps(payload, ensure_ascii=False) if args.json else f"Exported learner state to {args.path}")
        return 0

    if command == "import":
        from polyglot.data.pairs import stable_card_id
        from polyglot.learning_store import read_export

        known_cards = {pair.id: {stable_card_id(pair.id, entry) for entry in pair.phrases} for pair in ALL_PAIRS}
        imported = _learner_store().import_data(read_export(args.path), known_cards)
        payload = {"imported": imported}
        print(json.dumps(payload, ensure_ascii=False) if args.json else f"Imported {imported} learner cards.")
        return 0

    parser.error(f"unknown command: {command}")
    return 2
