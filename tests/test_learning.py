"""Focused contract tests for the local learning loop."""

from __future__ import annotations

import copy
import os
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from polyglot.data.content_loader import get_pair
from polyglot.data.pairs import PhraseEntry, stable_card_id
from polyglot.learning_store import (
    LearnerStore,
    _chmod_private_file_if_present,
    _local_day_start,
    read_export,
    write_export,
)
from polyglot.review import (
    LEARNING_STAGE_ORDER,
    build_review_session,
    compact_ambient_line,
    due_ambient_card,
)
from polyglot.scheduler import AGAIN_SECONDS, DAY_SECONDS, MAX_INTERVAL_SECONDS, ScheduleState, schedule


class SchedulerTests(unittest.TestCase):
    def test_ratified_intervals_and_lapse_are_deterministic(self) -> None:
        now = 1_000.0
        again = schedule(None, "again", now)
        self.assertEqual(again.interval_seconds, AGAIN_SECONDS)
        self.assertEqual(again.due_at, now + AGAIN_SECONDS)
        self.assertEqual(again.lapses, 1)
        hard = schedule(ScheduleState(due_at=now, interval_seconds=DAY_SECONDS), "hard", now)
        self.assertEqual(hard.interval_seconds, int(DAY_SECONDS * 1.2))
        self.assertEqual(schedule(None, "good", now).interval_seconds, DAY_SECONDS)
        self.assertEqual(schedule(None, "easy", now).interval_seconds, 4 * DAY_SECONDS)
        capped = schedule(ScheduleState(due_at=now, interval_seconds=MAX_INTERVAL_SECONDS), "easy", now)
        self.assertEqual(capped.interval_seconds, MAX_INTERVAL_SECONDS)

    def test_one_hundred_replays_match_after_restart(self) -> None:
        grades = ("again", "hard", "good", "easy") * 25
        state = None
        now = 0.0
        for grade in grades:
            state = schedule(state, grade, now)
            now = state.due_at
        replay = None
        now = 0.0
        for grade in grades:
            replay = schedule(replay, grade, now)
            now = replay.due_at
        self.assertEqual(state, replay)


class LearningStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = LearnerStore(self.root / "learner")
        self.pair = get_pair("en-de")
        self.card_id = stable_card_id(self.pair.id, self.pair.phrases[0])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_progress_survives_restart_and_pair_switch(self) -> None:
        state = self.store.record_grade(self.pair.id, self.card_id, "forward", "again", 0)
        self.assertLessEqual(state.due_at, 24 * 60 * 60)
        second = LearnerStore(self.root / "learner")
        self.assertEqual(second.get_state(self.pair.id, self.card_id, "forward"), state)
        self.assertEqual(second.progress("en-ja", 0)["tracked"], 0)

    def test_session_is_due_first_new_second_and_never_repeats(self) -> None:
        for entry in self.pair.phrases[:4]:
            self.store.record_grade(self.pair.id, stable_card_id(self.pair.id, entry), "forward", "good", 0)
        cards = build_review_session(self.store, self.pair, "forward", DAY_SECONDS + 1)
        self.assertEqual(len(cards), 5)
        self.assertEqual(len({card.card_id for card in cards}), 5)
        self.assertEqual({card.card_id for card in cards[:4]}, {stable_card_id(self.pair.id, entry) for entry in self.pair.phrases[:4]})

    def test_fresh_german_session_follows_declared_stage_then_catalog_order(self) -> None:
        stage_rank = {
            stage: index for index, stage in enumerate(LEARNING_STAGE_ORDER)
        }
        expected_entries = sorted(
            enumerate(self.pair.phrases),
            key=lambda item: (
                stage_rank[item[1].metadata["learning_stage"]],
                item[0],
            ),
        )

        cards = build_review_session(
            self.store,
            self.pair,
            "forward",
            0,
            limit=40,
        )

        self.assertEqual(
            [card.card_id for card in cards],
            [
                stable_card_id(self.pair.id, entry)
                for _, entry in expected_entries[:40]
            ],
        )
        self.assertEqual(len({card.card_id for card in cards}), len(cards))

    def test_export_import_forget_and_permissions(self) -> None:
        self.store.record_grade(self.pair.id, self.card_id, "forward", "good", 0)
        destination = self.root / "state.json"
        write_export(destination, self.store.export_data())
        self.assertEqual(read_export(destination)["schema_version"], 1)
        if os.name != "nt":
            self.assertEqual((destination.stat().st_mode & 0o777), 0o600)
            self.assertEqual(((self.root / "learner").stat().st_mode & 0o777), 0o700)
        other = LearnerStore(self.root / "other")
        self.assertEqual(other.import_data(read_export(destination), {self.pair.id: {self.card_id}}), 1)
        self.assertEqual(other.forget(self.pair.id), 1)

    def test_export_preserves_existing_parent_permissions(self) -> None:
        destination_dir = self.root / "shared-export"
        destination_dir.mkdir(mode=0o755)
        if os.name != "nt":
            destination_dir.chmod(0o755)
        write_export(destination_dir / "state.json", self.store.export_data())
        if os.name != "nt":
            self.assertEqual(destination_dir.stat().st_mode & 0o777, 0o755)

    def test_import_rejects_impossible_state_without_partial_writes(self) -> None:
        self.store.record_grade(self.pair.id, self.card_id, "forward", "good", 1)
        original = self.store.export_data()
        invalid_fields = {
            "due_at": float("inf"),
            "interval_seconds": -1,
            "repetitions": -1,
            "lapses": -1,
            "last_seen_at": "not-a-time",
            "difficulty": 99,
            "mode": "arbitrary",
        }
        other = LearnerStore(self.root / "import-target")
        known = {self.pair.id: {self.card_id}}
        for field, value in invalid_fields.items():
            with self.subTest(field=field):
                payload = copy.deepcopy(original)
                payload["card_state"][0][field] = value
                with self.assertRaises(ValueError):
                    other.import_data(payload, known)
                self.assertEqual(other.progress(None, 1)["tracked"], 0)
        payload = copy.deepcopy(original)
        payload["card_state"][0]["interval_seconds"] = 1.9
        with self.assertRaises(ValueError):
            other.import_data(payload, known)
        payload = copy.deepcopy(original)
        payload["preferences"] = [{"pair_id": "unknown-pair", "daily_goal": 5}]
        with self.assertRaises(ValueError):
            other.import_data(payload, known)
        self.assertEqual(other.progress(None, 1)["tracked"], 0)
        payload = copy.deepcopy(original)
        payload["card_state"][0]["repetitions"] = True
        with self.assertRaises(ValueError):
            other.import_data(payload, known)
        payload = copy.deepcopy(original)
        payload["preferences"] = [{"pair_id": self.pair.id, "daily_goal": "7"}]
        with self.assertRaises(ValueError):
            other.import_data(payload, known)
        self.assertEqual(other.progress(None, 1)["tracked"], 0)

    @unittest.skipUnless(hasattr(time, "tzset"), "requires POSIX timezone control")
    def test_progress_day_boundary_uses_the_learner_timezone(self) -> None:
        previous = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "Asia/Kolkata"
            time.tzset()
            instant = datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc).timestamp()
            expected = datetime(2026, 1, 1, 18, 30, tzinfo=timezone.utc).timestamp()
            self.assertEqual(_local_day_start(instant), expected)
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    @unittest.skipUnless(hasattr(time, "tzset"), "requires POSIX timezone control")
    def test_progress_day_boundary_respects_dst_transition_offset(self) -> None:
        previous = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "America/New_York"
            time.tzset()
            cases = (
                (
                    datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2026, 3, 8, 5, 0, tzinfo=timezone.utc).timestamp(),
                ),
                (
                    datetime(2026, 11, 1, 7, 30, tzinfo=timezone.utc).timestamp(),
                    datetime(2026, 11, 1, 4, 0, tzinfo=timezone.utc).timestamp(),
                ),
            )
            for instant, expected in cases:
                with self.subTest(instant=instant):
                    self.assertEqual(_local_day_start(instant), expected)
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_stable_id_ignores_catalog_position_and_handles_scripts(self) -> None:
        entry = PhraseEntry(source=" नमस्ते ", target="你好", pronunciation="x")
        self.assertEqual(stable_card_id("en-hi", entry), stable_card_id("en-hi", PhraseEntry(source="नमस्ते", target="你好")))
        self.assertNotEqual(stable_card_id("en-hi", entry), stable_card_id("en-zh", entry))

    def test_due_ambient_read_does_not_change_schedule_or_exceed_budget(self) -> None:
        self.store.record_grade(self.pair.id, self.card_id, "forward", "good", 0)
        before = self.store.get_state(self.pair.id, self.card_id, "forward")
        card = due_ambient_card(self.store, self.pair, DAY_SECONDS + 1)
        self.assertIsNotNone(card)
        line = compact_ambient_line(card)
        self.assertIsNotNone(line)
        self.assertLessEqual(len(line), 180)
        self.assertLessEqual(len(line.split()), 80)
        self.assertEqual(before, self.store.get_state(self.pair.id, self.card_id, "forward"))

    def test_concurrent_grades_commit_without_dropping_cards(self) -> None:
        card_ids = [stable_card_id(self.pair.id, entry) for entry in self.pair.phrases[:20]]

        def grade(card_id: str) -> None:
            LearnerStore(self.root / "learner").record_grade(self.pair.id, card_id, "forward", "good", 0)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(grade, card_ids))
        self.assertEqual(self.store.progress(self.pair.id, 0)["tracked"], len(card_ids))
        with self.store._session() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM review_history").fetchone()[0], len(card_ids))

    def test_sqlite_sidecar_can_disappear_before_permission_hardening(self) -> None:
        _chmod_private_file_if_present(self.root / "learner" / "learning.sqlite3-shm")

    def test_corrupt_or_newer_state_is_quarantined_with_one_notice(self) -> None:
        self.store.path.write_bytes(b"not a sqlite database")
        recovered = LearnerStore(self.root / "learner")
        self.assertTrue(recovered.was_quarantined)
        self.assertTrue(recovered.consume_quarantine_notice())
        self.assertFalse(recovered.consume_quarantine_notice())
        self.assertTrue(list((self.root / "learner").glob("learning.sqlite3.corrupt-*")))

    def test_german_cloze_uses_original_german_context_and_keeps_typed_recall(self) -> None:
        german = next(entry for entry in self.pair.phrases if entry.metadata.get("cloze"))
        # Validate the v2 routing directly through its card constructor.
        from polyglot.review import _card
        routed = _card(self.pair, german, "cloze")
        self.assertIn("_____", routed.prompt)
        self.assertEqual(routed.answer, german.metadata["cloze"]["answer_text"])
        self.assertEqual(german.metadata["production_prompt"]["mode"], "typed_recall")


if __name__ == "__main__":
    unittest.main()
