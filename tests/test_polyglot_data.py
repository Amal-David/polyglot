"""Polyglot data integrity tests — registered directions must shape up."""

from __future__ import annotations

import subprocess
import sys
import unicodedata
import unittest
from pathlib import Path

from polyglot.data.content_loader import ALL_PAIRS, get_pair, list_pairs
from polyglot.data.content_v2 import STAGING_MANIFEST, STAGING_VALIDATION_REPORT, validate_v2_content
from polyglot.data.pairs import CATEGORIES, LanguagePair, PhraseEntry, load_pair
from polyglot.review import _card, compact_ambient_line
from polyglot.safety import AMBIENT_MAX_CHARACTERS, AMBIENT_MAX_TOKENS, approximate_token_count
from polyglot.safety import contains_control_or_sensitive_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PAIR_COUNT = 74
EXPECTED_ENTRY_COUNT = 19_281
MIN_PHRASES_PER_PAIR = 200


class PolyglotDataIntegrity(unittest.TestCase):
    def test_every_catalog_card_has_a_safe_bounded_ambient_rendering(self) -> None:
        lines = [
            compact_ambient_line(_card(pair, entry, "forward"))
            for pair in ALL_PAIRS
            for entry in pair.phrases
        ]
        self.assertNotIn(None, lines)
        self.assertEqual(max(map(len, lines)), 85)
        self.assertEqual(max(map(approximate_token_count, lines)), 43)
        self.assertTrue(all(len(line) <= AMBIENT_MAX_CHARACTERS for line in lines))
        self.assertTrue(all(approximate_token_count(line) <= AMBIENT_MAX_TOKENS for line in lines))

    def test_catalog_has_no_control_or_host_context_sentinels(self) -> None:
        unsafe = [
            (pair.id, field, value)
            for pair in ALL_PAIRS
            for entry in pair.phrases
            for field, value in (("source", entry.source), ("target", entry.target), ("pronunciation", entry.pronunciation), ("note", entry.note))
            if contains_control_or_sensitive_data(value)
        ]
        self.assertEqual(unsafe, [])
    def test_loads_exact_release_catalog(self) -> None:
        self.assertEqual(EXPECTED_PAIR_COUNT, len(ALL_PAIRS))
        self.assertEqual(EXPECTED_PAIR_COUNT, len(list_pairs()))
        self.assertEqual(
            sum(len(pair.phrases) for pair in ALL_PAIRS),
            EXPECTED_ENTRY_COUNT,
        )

    def test_pair_ids_are_unique(self) -> None:
        ids = [p.id for p in ALL_PAIRS]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate pair ids: {ids}")

    def test_get_pair_round_trips(self) -> None:
        for p in ALL_PAIRS:
            self.assertIs(p, get_pair(p.id))
        self.assertIsNone(get_pair("does-not-exist"))

    def test_lazy_load_pair_matches_registry(self) -> None:
        # Includes the German (annotate_german_pair) and four mechanically
        # reversed directions (build_reverse_pairs), not just bare-module pairs.
        for p in ALL_PAIRS:
            self.assertIs(p, load_pair(p.id))
        self.assertIsNone(load_pair("does-not-exist"))
        self.assertIsNone(load_pair("EN-DE"))
        self.assertIsNone(load_pair("en.de"))
        self.assertIsNone(load_pair(""))

    def test_hook_path_imports_only_the_active_pair(self) -> None:
        code = (
            "import sys; from polyglot.data.pairs import load_pair; "
            "pair = load_pair('en-es'); assert pair and pair.id == 'en-es'; "
            "assert 'polyglot.data.content_loader' not in sys.modules; "
            "loaded = sorted(m for m in sys.modules if m.startswith('polyglot.data.pair_')); "
            "assert loaded == ['polyglot.data.pair_en_es'], loaded"
        )
        subprocess.run([sys.executable, "-c", code], check=True, cwd=PROJECT_ROOT)

    def test_hook_path_falls_back_to_registry_for_derived_pairs(self) -> None:
        code = (
            "import sys; from polyglot.data.pairs import load_pair; "
            "pair = load_pair('pl-en'); assert pair and pair.id == 'pl-en'; "
            "assert 'polyglot.data.content_loader' in sys.modules"
        )
        subprocess.run([sys.executable, "-c", code], check=True, cwd=PROJECT_ROOT)

    def test_each_pair_meets_minimum_phrase_budget(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                self.assertGreaterEqual(
                    len(pair.phrases),
                    MIN_PHRASES_PER_PAIR,
                    f"{pair.id} only has {len(pair.phrases)} phrases",
                )

    def test_phrase_entries_have_required_fields(self) -> None:
        for pair in ALL_PAIRS:
            for idx, entry in enumerate(pair.phrases):
                with self.subTest(pair=pair.id, idx=idx):
                    self.assertIsInstance(entry, PhraseEntry)
                    self.assertTrue(entry.source.strip(), f"empty source in {pair.id}[{idx}]")
                    self.assertTrue(entry.target.strip(), f"empty target in {pair.id}[{idx}]")
                    self.assertTrue(entry.pronunciation.strip(), f"empty pronunciation in {pair.id}[{idx}]")
                    self.assertIn(
                        entry.category,
                        CATEGORIES,
                        f"unknown category {entry.category!r} in {pair.id}[{idx}]",
                    )
                    self.assertTrue(entry.subcategory.strip(), f"empty subcategory in {pair.id}[{idx}]")

    def test_no_duplicate_targets_within_a_pair(self) -> None:
        for pair in ALL_PAIRS:
            targets = [e.target for e in pair.phrases]
            with self.subTest(pair=pair.id):
                self.assertEqual(
                    len(targets),
                    len(set(targets)),
                    f"duplicate targets within {pair.id}",
                )

    def test_pair_metadata_is_populated(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                self.assertIsInstance(pair, LanguagePair)
                self.assertTrue(pair.id)
                self.assertTrue(pair.source_lang)
                self.assertTrue(pair.target_lang)
                self.assertTrue(pair.target_native)
                self.assertTrue(pair.script)
                self.assertTrue(pair.flag)
                self.assertTrue(pair.blurb)

    def test_each_pair_starts_with_a_script_entry_carrying_a_note(self) -> None:
        for pair in ALL_PAIRS:
            with self.subTest(pair=pair.id):
                first_script = next(
                    (e for e in pair.phrases if e.category == "script"), None
                )
                self.assertIsNotNone(first_script, f"no script entry in {pair.id}")
                self.assertTrue(
                    first_script.note.strip(),
                    f"first script entry of {pair.id} should carry a pronunciation note",
                )

    def test_v2_staging_metadata_and_reverse_direction_release_gates(self) -> None:
        report = validate_v2_content(ALL_PAIRS)
        self.assertEqual(report["direction_count"], EXPECTED_PAIR_COUNT)
        self.assertEqual(report["entry_count"], EXPECTED_ENTRY_COUNT)
        self.assertEqual(report["german_record_count"], 520)
        self.assertTrue(report["minimum_250_each"])
        self.assertTrue(report["unique_record_ids"])
        self.assertTrue(report["original_script_preserved"])
        self.assertTrue(all(report["reverse_scripts"].values()))
        self.assertTrue(report["not_native_reviewed"])
        self.assertGreaterEqual(report["german_article_gender_coverage"], 100)
        self.assertGreaterEqual(report["german_cloze_coverage"], 70)
        self.assertEqual(STAGING_MANIFEST["artifacts"]["german-path-v1.jsonl"]["records"], 520)
        self.assertEqual(STAGING_MANIFEST["artifacts"]["reverse-directions-v1.jsonl"]["records"], 1_046)
        self.assertEqual(report["reverse_counts"], STAGING_VALIDATION_REPORT["reverse_counts"])
        self.assertEqual(report["reverse_record_count"], STAGING_VALIDATION_REPORT["reverse_record_count"])

    def test_reverse_records_preserve_the_exact_shipped_source_and_german_cards_keep_ids(self) -> None:
        source_by_reverse = {"pl-en": "en-pl", "uk-en": "en-uk", "sv-en": "en-sv", "el-en": "en-el"}
        for reverse_id, source_id in source_by_reverse.items():
            for source, reversed_entry in zip(get_pair(source_id).phrases, get_pair(reverse_id).phrases):
                self.assertEqual((reversed_entry.source, reversed_entry.target), (source.target, source.source))
                self.assertEqual(reversed_entry.metadata["provenance"]["source_pair_id"], source_id)
        from polyglot.data.pair_en_de import PAIR as raw_german
        from polyglot.data.pairs import stable_card_id
        annotated = get_pair("en-de").phrases[0]
        self.assertEqual(stable_card_id("en-de", annotated), stable_card_id("en-de", raw_german.phrases[0]))

    def test_original_scripts_remain_available_across_catalog_and_reverse_paths(self) -> None:
        fixtures = {
            "pl-en": ("source", "Latin"),
            "uk-en": ("source", "Cyrillic"),
            "el-en": ("source", "Greek"),
            "en-ja": ("target", "CJK"),
            "en-hi": ("target", "Indic"),
            "en-th": ("target", "Thai"),
            "en-ar": ("target", "RTL"),
        }
        for pair_id, (side, label) in fixtures.items():
            pair = get_pair(pair_id)
            self.assertIsNotNone(pair)
            text = "\n".join(getattr(entry, side) for entry in pair.phrases)
            self.assertEqual(text, unicodedata.normalize("NFC", text), f"{label} fixture changed")
            self.assertTrue(any(ord(char) > 127 for char in text), f"{label} fixture lost original script")


if __name__ == "__main__":
    unittest.main()
