"""Hermes Agent plugin registration."""

from __future__ import annotations

from pathlib import Path

from polyglot.ambient import (
    format_companion_message,
    next_ambient_message,
    sample_phrase,
)
from polyglot.data.content_loader import get_pair
from polyglot.storage import get_active_pair_id, load_config, save_config, set_active_pair_id


def transform_llm_output(response_text: str, **_kwargs) -> str | None:
    """Append an opted-in phrase while preserving the original response."""
    try:
        message = next_ambient_message("hermes")
    except Exception:
        return None
    if not message:
        return None
    return f"{response_text.rstrip()}\n\n{message}"


def handle_command(raw_args: str) -> str:
    """Handle `/polyglot` without invoking the model or editing Hermes config."""
    try:
        parts = raw_args.split()
        action = parts[0].lower() if parts else "status"
        if action == "status":
            config = load_config()
            state = "enabled" if config.get("ambient_enabled") else "disabled"
            return (
                f"Polyglot ambient mode is {state}; pair "
                f"{config.get('active_pair_id') or '(none)'}, cadence "
                f"{int(config.get('ambient_cadence', 5) or 5)}."
            )
        if action == "disable":
            config = load_config()
            config["ambient_enabled"] = False
            save_config(config)
            return "Polyglot ambient mode disabled."
        if action == "sample":
            pair_id = parts[1] if len(parts) > 1 else get_active_pair_id()
            phrase = sample_phrase(pair_id)
            return (
                format_companion_message(phrase)
                if phrase
                else "Select a valid pair first, for example: /polyglot enable en-es"
            )
        if action in {"enable", "pair"}:
            if len(parts) < 2 or get_pair(parts[1]) is None:
                return "Usage: /polyglot enable <pair-id> [cadence]"
            cadence = None
            if action == "enable" and len(parts) > 2:
                cadence = int(parts[2])
                if cadence < 1:
                    raise ValueError
            set_active_pair_id(parts[1])
            config = load_config()
            if action == "enable":
                config["ambient_enabled"] = True
                if cadence is not None:
                    config["ambient_cadence"] = cadence
            save_config(config)
            return handle_command("status")
    except Exception:
        return "Usage: /polyglot [status|sample [pair]|enable <pair> [cadence]|disable]"
    return "Usage: /polyglot [status|sample [pair]|enable <pair> [cadence]|disable]"


def register(ctx) -> None:
    """Register the output transform and canonical skill with Hermes."""
    ctx.register_hook("transform_llm_output", transform_llm_output)
    skill_path = Path(__file__).resolve().parents[1] / "skills" / "polyglot" / "SKILL.md"
    if skill_path.is_file():
        ctx.register_skill("polyglot", skill_path)
    ctx.register_command(
        "polyglot",
        handler=handle_command,
        description="Sample a phrase or configure Polyglot ambience",
        args_hint="[status|sample|enable|disable]",
    )
