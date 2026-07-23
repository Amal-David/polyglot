"""Polyglot ambient hook tests — picker variety + cadence gating."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import polyglot.skill.config as polyglot_config
import polyglot.storage as polyglot_storage
from polyglot.skill.phrase_picker import (
    RECENT_WINDOW,
    pick_phrase,
    select_phrase_index,
    total_phrase_count,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _with_isolated_state(test_method):
    """Decorator: route hook state + polyglot config to a tempdir."""

    def wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            self._isolated_dir = tmp_path
            state_file = tmp_path / "hook_state.json"

            real_load_config = polyglot_storage.load_config
            real_save_config = polyglot_storage.save_config
            real_update_config = polyglot_storage.update_config

            def fake_load_config(base_dir=None):
                return real_load_config(tmp_path)

            def fake_save_config(cfg, base_dir=None):
                real_save_config(cfg, tmp_path)

            def fake_update_config(mutator, base_dir=None):
                return real_update_config(mutator, tmp_path)

            with patch.object(polyglot_config, "HOOK_STATE_FILE", state_file), \
                 patch.object(polyglot_storage, "load_config", fake_load_config), \
                 patch.object(polyglot_storage, "save_config", fake_save_config), \
                 patch.object(polyglot_storage, "update_config", fake_update_config):
                test_method(self)

    return wrapper


class PhrasePickerVarietyTests(unittest.TestCase):
    def test_unseen_phrases_picked_before_repeats(self) -> None:
        phrases = list(range(5))  # length is what matters
        shown_counts = {"0": 2, "1": 1, "2": 0, "3": 0, "4": 0}
        recent = []
        idx = select_phrase_index(phrases, shown_counts, recent)
        self.assertIn(idx, {2, 3, 4})

    def test_recent_phrases_deprioritized(self) -> None:
        phrases = list(range(5))
        shown_counts: dict[str, int] = {}
        recent = [0, 1, 2]
        seen_outside_recent = 0
        for _ in range(40):
            idx = select_phrase_index(phrases, shown_counts, recent)
            if idx in (3, 4):
                seen_outside_recent += 1
        self.assertGreater(seen_outside_recent, 30)

    def test_recent_window_constant_is_finite(self) -> None:
        self.assertGreaterEqual(RECENT_WINDOW, 10)

    def test_select_phrase_index_rejects_empty_phrases(self) -> None:
        with self.assertRaises(ValueError):
            select_phrase_index([], {}, [])


class HookEndToEndTests(unittest.TestCase):
    @_with_isolated_state
    def test_pick_phrase_returns_none_without_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id(None)
        self.assertIsNone(pick_phrase())

    @_with_isolated_state
    def test_pick_phrase_picks_from_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        result = pick_phrase()
        self.assertIsNotNone(result)
        self.assertEqual(result["pair_id"], "en-es")
        self.assertEqual(result["pair_label"], "English → Spanish")
        self.assertTrue(result["target"])
        self.assertEqual(result["unique_shown"], 1)

    @_with_isolated_state
    def test_pick_phrase_increments_shown_counts(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        for _ in range(3):
            pick_phrase()
        state = polyglot_config.load_hook_state()
        self.assertEqual(state["total_phrases_shown"], 3)
        self.assertEqual(sum(state["shown_counts"].values()), 3)

    @_with_isolated_state
    def test_switching_pair_resets_history(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        for _ in range(4):
            pick_phrase()
        state_a = polyglot_config.load_hook_state()
        self.assertEqual(state_a["total_phrases_shown"], 4)

        polyglot_storage.set_active_pair_id("en-ja")
        result = pick_phrase()
        self.assertEqual(result["pair_id"], "en-ja")
        state_b = polyglot_config.load_hook_state()
        # New pair → history is freshly reset and only the latest pick counts.
        self.assertEqual(state_b["total_phrases_shown"], 1)
        self.assertEqual(state_b["active_pair_id"], "en-ja")

    @_with_isolated_state
    def test_total_phrase_count_matches_pair_data(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        from polyglot.data.content_loader import get_pair
        self.assertEqual(total_phrase_count(), len(get_pair("en-es").phrases))


class HookScriptTests(unittest.TestCase):
    """Smoke-test the shared opt-in Stop hook protocol."""

    @_with_isolated_state
    def test_hook_returns_empty_when_no_active_pair(self) -> None:
        polyglot_storage.set_active_pair_id(None)
        import polyglot.ambient as ambient
        with patch("builtins.print") as mock_print:
            ambient.main(["--hook", "--host", "claude"])
        printed = mock_print.call_args[0][0]
        self.assertEqual(json.loads(printed), {})

    @_with_isolated_state
    def test_hook_returns_empty_off_cadence(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        cfg = polyglot_storage.load_config()
        cfg["ambient_enabled"] = True
        cfg["ambient_cadence"] = 5
        polyglot_storage.save_config(cfg)
        import polyglot.ambient as ambient
        with patch("builtins.print") as mock_print:
            ambient.main(["--hook", "--host", "claude"])
        printed = mock_print.call_args[0][0]
        self.assertEqual(json.loads(printed), {})

    @_with_isolated_state
    def test_hook_emits_system_message_on_cadence(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")
        cfg = polyglot_storage.load_config()
        cfg["ambient_enabled"] = True
        cfg["ambient_cadence"] = 1
        polyglot_storage.save_config(cfg)
        from polyglot.data.content_loader import get_pair
        from polyglot.data.pairs import stable_card_id
        from polyglot.learning_store import LearnerStore

        pair = get_pair("en-es")
        card_id = stable_card_id(pair.id, pair.phrases[0])
        learner_dir = self._isolated_dir / "learner"
        learner = LearnerStore(learner_dir)
        learner.record_grade(pair.id, card_id, "forward", "good", 0)
        before = learner.get_state(pair.id, card_id, "forward")
        import polyglot.ambient as ambient
        with patch("polyglot.ambient.learner_data_dir", return_value=learner_dir), \
             patch("builtins.print") as mock_print:
            ambient.main(["--hook", "--host", "claude"])
        printed = mock_print.call_args[0][0]
        payload = json.loads(printed)
        self.assertIn("systemMessage", payload)
        self.assertIn("Polyglot due", payload["systemMessage"])
        self.assertLessEqual(len(payload["systemMessage"]), 180)
        self.assertEqual(before, learner.get_state(pair.id, card_id, "forward"))

    @_with_isolated_state
    def test_fresh_pair_gets_one_ungraded_starter_then_waits_for_review(self) -> None:
        polyglot_storage.set_active_pair_id("en-de")
        cfg = polyglot_storage.load_config()
        cfg["ambient_enabled"] = True
        cfg["ambient_cadence"] = 1
        polyglot_storage.save_config(cfg)

        from polyglot.learning_store import LearnerStore
        import polyglot.ambient as ambient

        learner = LearnerStore(self._isolated_dir / "learner")
        with patch(
            "polyglot.ambient.learner_data_dir",
            return_value=self._isolated_dir / "learner",
        ), patch("polyglot.ambient.time.time", return_value=1_000):
            first = ambient.next_ambient_message("claude")
            second = ambient.next_ambient_message("claude")

        self.assertIsNotNone(first)
        self.assertIn("Polyglot starter", first)
        self.assertIn("hello → hallo", first)
        self.assertIsNone(second)
        self.assertEqual(learner.progress("en-de", 1_000)["tracked"], 0)
        with learner._session() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM review_history").fetchone()[0],
                0,
            )

    @_with_isolated_state
    def test_tracked_pair_without_due_card_never_falls_back_to_starter(self) -> None:
        polyglot_storage.set_active_pair_id("en-de")
        cfg = polyglot_storage.load_config()
        cfg["ambient_enabled"] = True
        cfg["ambient_cadence"] = 1
        polyglot_storage.save_config(cfg)

        from polyglot.data.content_loader import get_pair
        from polyglot.data.pairs import stable_card_id
        from polyglot.learning_store import LearnerStore
        import polyglot.ambient as ambient

        pair = get_pair("en-de")
        learner = LearnerStore(self._isolated_dir / "learner")
        card_id = stable_card_id(pair.id, pair.phrases[0])
        learner.record_grade(pair.id, card_id, "forward", "good", 1_000)
        before = learner.get_state(pair.id, card_id, "forward")

        with patch(
            "polyglot.ambient.learner_data_dir",
            return_value=self._isolated_dir / "learner",
        ), patch("polyglot.ambient.time.time", return_value=1_001):
            self.assertIsNone(ambient.next_ambient_message("claude"))

        self.assertEqual(before, learner.get_state(pair.id, card_id, "forward"))
        self.assertNotIn(
            "en-de",
            polyglot_config.load_hook_state().get("ambient_starter_pairs", {}),
        )


class HookImportCostTests(unittest.TestCase):
    """The Stop hook (scripts/ambient.py) runs on every completed agent turn;
    importing polyglot.ambient must not eagerly load the full pair registry."""

    def test_importing_ambient_does_not_load_the_full_registry(self) -> None:
        code = (
            "import sys; import polyglot.ambient; "
            "assert 'polyglot.data.content_loader' not in sys.modules"
        )
        subprocess.run([sys.executable, "-c", code], check=True, cwd=PROJECT_ROOT)


class HookSeedDeterminismTests(unittest.TestCase):
    """POLYGLOT_HOOK_SEED lets scripted demo recordings get reproducible picks."""

    @_with_isolated_state
    def test_same_seed_produces_the_same_phrase_pick(self) -> None:
        import polyglot.ambient as ambient

        polyglot_storage.set_active_pair_id("en-es")

        with patch.dict("os.environ", {"POLYGLOT_HOOK_SEED": "2"}), patch("builtins.print"):
            ambient.main(["--sample", "--pair", "en-es", "--json"])
            first_state = dict(polyglot_config.load_hook_state())

        polyglot_config.save_hook_state({})
        with patch.dict("os.environ", {"POLYGLOT_HOOK_SEED": "2"}), patch("builtins.print"):
            ambient.main(["--sample", "--pair", "en-es", "--json"])
            second_state = dict(polyglot_config.load_hook_state())

        self.assertEqual(first_state["last_phrase_idx"], second_state["last_phrase_idx"])


class HookStateConcurrencyTests(unittest.TestCase):
    """Verifies the existing locked_file-backed update_hook_state under load."""

    @_with_isolated_state
    def test_concurrent_phrase_picks_do_not_lose_updates(self) -> None:
        polyglot_storage.set_active_pair_id("en-es")

        with ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(lambda _: pick_phrase(), range(30)))

        state = polyglot_config.load_hook_state()
        self.assertEqual(state["total_phrases_shown"], 30)
        self.assertEqual(sum(state["shown_counts"].values()), 30)


if __name__ == "__main__":
    unittest.main()
