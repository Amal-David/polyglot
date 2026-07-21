"""Out-of-curses activation flow for the optional ambient mode."""

from __future__ import annotations

from polyglot.data.pairs import LanguagePair
from polyglot.storage import load_config, save_config, set_active_pair_id


def run_install_flow(
    pair: LanguagePair,
    *,
    auto_confirm: bool = False,
    print_only: bool = False,
) -> list:
    """Select a pair and optionally enable ambience without editing host config."""
    print()
    print("╔══════════════════════════════════════════════╗")
    print(f"║  Polyglot ambient — {pair.source_lang} → {pair.target_lang}")
    print("╚══════════════════════════════════════════════╝")
    print()
    print("Agent plugins are installed separately. This only updates Polyglot's")
    print("own local configuration; it never edits an agent's settings file.")
    print()
    print(f"CLI equivalent: polyglot ambient enable --pair {pair.id}")

    if print_only:
        return []

    accepted = auto_confirm
    if not auto_confirm:
        try:
            accepted = input("Enable ambient phrases for this pair? [y/N] ").strip().lower() in {
                "y",
                "yes",
            }
        except EOFError:
            accepted = False
    if not accepted:
        print("No changes made.")
        return []

    set_active_pair_id(pair.id)
    config = load_config()
    config["ambient_enabled"] = True
    save_config(config)
    print(f"Ambient phrases enabled for {pair.id}.")
    try:
        input("Press Enter to return to the cabinet...")
    except EOFError:
        pass
    return []
