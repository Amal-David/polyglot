"""Focused fail-closed and privacy contracts at host boundaries."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from polyglot.hermes import transform_llm_output
from polyglot.ambient import next_ambient_message
from polyglot.review import ReviewCard, compact_ambient_line
from polyglot.safety import AMBIENT_MAX_CHARACTERS, AMBIENT_MAX_TOKENS, approximate_token_count
from polyglot.storage import data_dir, save_config


class HostBoundarySafetyTests(unittest.TestCase):
    def test_ambient_rejects_secret_sentinel_control_and_budget_overflow(self) -> None:
        base = dict(pair_id="en-es", card_id="pc1_test", direction="forward", hint="", mode="forward")
        for prompt, answer in (
            ("__POLYGLOT_SECRET_SENTINEL__", "hola"),
            ("hello\x00", "hola"),
            ("word " * 100, "hola"),
            ("x" * AMBIENT_MAX_CHARACTERS, "hola"),
        ):
            with self.subTest(prompt=prompt[:20]):
                self.assertIsNone(compact_ambient_line(ReviewCard(prompt=prompt, answer=answer, **base)))

    def test_ambient_payload_has_strict_character_and_token_budget(self) -> None:
        line = compact_ambient_line(ReviewCard(
            pair_id="en-es", card_id="pc1_test", direction="forward", prompt="hello", answer="hola", hint="", mode="forward"
        ))
        self.assertIsNotNone(line)
        self.assertLessEqual(len(line), AMBIENT_MAX_CHARACTERS)
        self.assertLessEqual(approximate_token_count(line), AMBIENT_MAX_TOKENS)

    def test_hermes_returns_no_transformation_when_disabled_or_malformed(self) -> None:
        for value in (None, "", "__POLYGLOT_SECRET_SENTINEL__", "safe\x00"):
            with self.subTest(value=value):
                with patch("polyglot.hermes.next_ambient_message", return_value=value):
                    self.assertIsNone(transform_llm_output("Original response"))

    def test_ambient_fails_closed_when_host_state_cannot_be_updated(self) -> None:
        with patch("polyglot.ambient.get_ambient_enabled", return_value=True), \
             patch("polyglot.ambient.get_active_pair_id", return_value="en-es"), \
             patch("polyglot.ambient.update_hook_state", return_value=None):
            self.assertIsNone(next_ambient_message("claude"))

    def test_config_home_is_private_and_does_not_include_environment_secrets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="polyglot-private-") as temporary:
            root = Path(temporary) / "state"
            save_config({"active_pair_id": "en-es"}, root)
            config = root / "config.json"
            self.assertNotIn("SECRET", config.read_text())
            if os.name != "nt":
                self.assertEqual((root.stat().st_mode & 0o777), 0o700)
                self.assertEqual((config.stat().st_mode & 0o777), 0o600)


if __name__ == "__main__":
    unittest.main()
