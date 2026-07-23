"""Local persistence for polyglot config and the active language pair.

Ambient-hook progress state (shown counts, cadence counters) lives in
polyglot.skill.config's hook_state.json, not here.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from polyglot.platform import app_data_dir, atomic_write_json, locked_file, private_directory

APP_DIR_NAME = "polyglot"
CONFIG_FILE = "config.json"
LEARNER_DIR = "learner"

DEFAULT_CONFIG = {
    "active_pair_id": None,
    "ambient_enabled": False,
    "ambient_cadence": 5,
    "phrase_cadence": 5,
    "codex_phrase_cadence": 5,
    "last_browsed_pair_id": None,
    "pair_history": [],
}


def data_dir(base_dir: Path | None = None) -> Path:
    return private_directory(app_data_dir(APP_DIR_NAME, base_dir))


def learner_data_dir(base_dir: Path | None = None) -> Path:
    """Return the isolated durable learner state directory.

    Config and legacy ambient state deliberately remain compatible JSON.  The
    learning database has a stricter storage boundary and is only opened by
    ``polyglot.learning_store``.
    """
    return data_dir(base_dir) / LEARNER_DIR


def _load_json(filename: str, defaults, base_dir: Path | None = None):
    path = data_dir(base_dir) / filename
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError):
        return copy.deepcopy(defaults)
    if isinstance(defaults, dict):
        if not isinstance(payload, dict):
            return copy.deepcopy(defaults)
        merged = copy.deepcopy(defaults)
        merged.update(payload)
        return merged
    return payload


def _save_json(filename: str, payload, base_dir: Path | None = None) -> None:
    path = data_dir(base_dir) / filename
    atomic_write_json(path, payload)


def update_config(mutator, base_dir: Path | None = None) -> dict:
    """Apply a config update under one lock so concurrent host turns survive."""
    root = data_dir(base_dir)
    with locked_file(root / ".config.lock"):
        config = _load_json(CONFIG_FILE, DEFAULT_CONFIG, base_dir)
        mutator(config)
        _save_json(CONFIG_FILE, config, base_dir)
        return config


def load_config(base_dir: Path | None = None) -> dict:
    return _load_json(CONFIG_FILE, DEFAULT_CONFIG, base_dir)


def save_config(config: dict, base_dir: Path | None = None) -> None:
    _save_json(CONFIG_FILE, config, base_dir)


def get_active_pair_id(base_dir: Path | None = None) -> str | None:
    config = load_config(base_dir)
    pair_id = config.get("active_pair_id")
    return pair_id if pair_id else None


def set_active_pair_id(pair_id: str | None, base_dir: Path | None = None) -> None:
    def apply(config: dict) -> None:
        config["active_pair_id"] = pair_id
        if pair_id:
            history = list(config.get("pair_history", []) if isinstance(config.get("pair_history"), list) else [])
            if pair_id in history:
                history.remove(pair_id)
            history.append(pair_id)
            config["pair_history"] = history[-20:]
            config["last_browsed_pair_id"] = pair_id

    update_config(apply, base_dir)
