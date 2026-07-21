"""Dataclasses for language pairs and phrase entries."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# Categories used across all language pair modules. The TUI and tests rely on
# these exact strings.
CATEGORIES = ("script", "vocab", "phrase", "sentence")

SUBCATEGORIES = (
    # script
    "alphabet",
    "syllabary",
    "tones",
    # numbers + time
    "numbers",
    "days",
    "months",
    "time",
    # vocab buckets
    "colors",
    "family",
    "food",
    "drink",
    "body",
    "weather",
    "animals",
    "house",
    "work",
    "verbs",
    "adjectives",
    "directions",
    "money",
    # phrase buckets
    "greeting",
    "courtesy",
    "introduction",
    "shopping",
    "restaurant",
    "transit",
    "emergency",
    # sentence buckets
    "question",
    "need",
    "opinion",
    "small_talk",
)


@dataclass(frozen=True)
class PhraseEntry:
    source: str
    target: str
    pronunciation: str = ""
    category: str = "vocab"
    subcategory: str = "verbs"
    note: str = ""
    # Optional, immutable catalog facts.  Keeping these alongside the entry
    # makes learning metadata available to terminal review without changing
    # legacy source/target/pronunciation callers.
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LanguagePair:
    id: str
    source_lang: str
    target_lang: str
    source_code: str
    target_code: str
    target_native: str
    script: str
    flag: str
    blurb: str
    phrases: tuple[PhraseEntry, ...] = field(default_factory=tuple)

    @property
    def label(self) -> str:
        return f"{self.source_lang} → {self.target_lang}"

    @property
    def display_native(self) -> str:
        return self.target_native or self.target_lang


def _canonical_text(value: str) -> str:
    """Normalize immutable card text without using mutable catalog position."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def stable_card_id(pair_id: str, entry: PhraseEntry) -> str:
    """Return the content identity used by learner progress across reorders.

    Pronunciation hints, notes, and category labels can be corrected or
    expanded without invalidating a learner's history.  The source/target
    meaning and pair direction are the durable identity until catalog records
    carry a declared ID of their own.
    """
    canonical = json.dumps(
        {"v": 1, "pair": pair_id, "source": _canonical_text(entry.source), "target": _canonical_text(entry.target)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "pc1_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
