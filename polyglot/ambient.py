"""Host-neutral ambient phrase delivery."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

from polyglot.data.content_loader import get_pair
from polyglot.skill.config import (
    get_active_pair_id,
    get_ambient_cadence,
    get_ambient_enabled,
    load_hook_state,
    save_hook_state,
    update_hook_state,
)
from polyglot.storage import learner_data_dir, load_config, set_active_pair_id, update_config
from polyglot.skill.phrase_picker import (
    format_phrase_message,
    pick_phrase,
    total_phrase_count,
)
from polyglot.safety import contains_control_or_sensitive_data

VALID_HOSTS = {"claude", "codex", "hermes", "pi"}


def detect_hook_host() -> str:
    """Identify Codex's compatibility environment, falling back to Claude."""
    return (
        "codex"
        if os.environ.get("PLUGIN_ROOT") or os.environ.get("CODEX_PLUGIN_ROOT")
        else "claude"
    )


def format_companion_message(phrase: dict[str, Any]) -> str:
    """Format a compact phrase card for agent and terminal surfaces."""
    if not _safe_phrase(phrase):
        return ""
    return format_phrase_message(
        phrase,
        total_phrase_count(phrase["pair_id"]),
        phrase["pair_label"],
    )


def next_ambient_message(host: str) -> str | None:
    """Return one due card or one fresh-pair starter at the configured cadence.

    Ambient delivery is never evidence of recall and cannot create or move a
    learner schedule.  The starter marker lives only in fail-soft hook state.
    """
    if host not in VALID_HOSTS:
        raise ValueError(f"unsupported host: {host}")
    if not get_ambient_enabled():
        return None

    pair_id = get_active_pair_id()
    if not pair_id:
        return None

    def increment(state: dict) -> None:
        counts = state.get("host_turn_counts")
        if not isinstance(counts, dict):
            counts = {}
        counts[host] = int(counts.get(host, 0) or 0) + 1
        state["host_turn_counts"] = counts

    state = update_hook_state(increment)
    if state is None:
        return None
    counts = state.get("host_turn_counts")
    if not isinstance(counts, dict):
        return None
    turn_count = int(counts.get(host, 0) or 0)

    cadence = get_ambient_cadence()
    if turn_count % cadence != 0:
        return None

    pair = get_pair(pair_id)
    if pair is None:
        return None
    from polyglot.learning_store import LearnerStore
    from polyglot.review import (
        compact_ambient_line,
        compact_starter_line,
        due_ambient_card,
        starter_ambient_card,
    )

    store = LearnerStore(learner_data_dir())
    # A corrupt or unknown database must never become host-visible ambient text.
    if store.was_quarantined:
        return None
    now = time.time()
    card = due_ambient_card(store, pair, now)
    if card:
        return compact_ambient_line(card)
    if store.progress(pair.id, now)["tracked"] > 0:
        return None

    starter = starter_ambient_card(pair)
    message = compact_starter_line(starter) if starter else None
    if not starter or not message:
        return None

    claimed = False

    def claim_starter(state: dict) -> None:
        nonlocal claimed
        pairs = state.get("ambient_starter_pairs")
        if not isinstance(pairs, dict):
            pairs = {}
        if pair.id not in pairs:
            pairs[pair.id] = starter.card_id
            claimed = True
        state["ambient_starter_pairs"] = pairs

    return message if update_hook_state(claim_starter) is not None and claimed else None


def ambient_learning_status(
    pair_id: str | None,
    *,
    now: float | None = None,
) -> dict[str, str]:
    """Describe the next truthful ambient learning state without changing it."""
    if not pair_id or get_pair(pair_id) is None:
        return {
            "learning_state": "waiting",
            "next_step": "Select a language pair before enabling ambient learning.",
        }

    from polyglot.learning_store import LearnerStore

    store = LearnerStore(learner_data_dir())
    current_time = time.time() if now is None else now
    progress = store.progress(pair_id, current_time)
    if progress["due"] > 0:
        return {
            "learning_state": "due-ready",
            "next_step": "The next cadence can show a due card without rescheduling it.",
        }
    if progress["tracked"] > 0:
        return {
            "learning_state": "waiting",
            "next_step": "No card is due yet; the learner schedule remains unchanged.",
        }

    starters = load_hook_state().get("ambient_starter_pairs")
    if isinstance(starters, dict) and pair_id in starters:
        return {
            "learning_state": "waiting",
            "next_step": f"Run `polyglot review --pair {pair_id}` to begin spaced repetition.",
        }
    return {
        "learning_state": "starter",
        "next_step": "The next cadence can show one ungraded starter exposure.",
    }


def sample_phrase(pair_id: str | None = None) -> dict[str, Any] | None:
    """Sample immediately, bypassing ambient enablement and cadence."""
    phrase = pick_phrase(pair_id)
    return phrase if _safe_phrase(phrase) else None


def _safe_phrase(phrase: object) -> bool:
    """Catalog facts may be rendered, never interpreted as host instructions."""
    if not isinstance(phrase, dict):
        return False
    fields = ("source", "target", "pronunciation", "note", "pair_id", "pair_label")
    return all(isinstance(phrase.get(field, ""), str) and not contains_control_or_sensitive_data(phrase.get(field, "")) for field in fields)


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
    if cadence is not None and cadence < 1:
        raise ValueError("cadence must be at least 1")

    def apply(config: dict) -> None:
        if cadence is not None:
            config["ambient_cadence"] = cadence
        if enabled is not None:
            if enabled and not config.get("active_pair_id"):
                raise ValueError("select a pair before enabling ambient mode")
            config["ambient_enabled"] = enabled

    if cadence is not None or enabled is not None:
        config = update_config(apply)
        changed = True
    else:
        config = load_config()
    payload = {
        "enabled": bool(config.get("ambient_enabled", False)),
        "active_pair": config.get("active_pair_id"),
        "cadence": int(config.get("ambient_cadence", 5) or 5),
    }
    payload.update(ambient_learning_status(payload["active_pair"]))
    return payload


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
