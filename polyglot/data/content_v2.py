"""Deterministic v2 learning metadata derived from shipped Polyglot content.

This is the in-package form of the reviewed T-0708 staging bundle.  It never
invents a translation, pronunciation, transliteration, or native review: it
only annotates German records and reverses the already-shipped source pairs.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

from .pairs import LanguagePair, PhraseEntry

SCHEMA_VERSION = "polyglot-content-staging/v1"
STAGING_MANIFEST = {
    "schema_version": SCHEMA_VERSION,
    "artifact_purpose": "machine_integrable_staging_only",
    "provenance_policy": "derived_only_no_new_translation",
    "reviewer_state": "not_native_reviewed",
    "artifacts": {
        "german-path-v1.jsonl": {"records": 520, "sha256": "847041c0bb2a9e3deac10106e1f408fae28cbd6d8af097be002a3023b9b790cc"},
        "reverse-directions-v1.jsonl": {"records": 1046, "sha256": "58c1d3e21d645d2f4e3760cf8c1c99a19cd94311ca09d21cd092e9880dca2abe"},
    },
}
STAGING_VALIDATION_REPORT = {
    "schema_version": SCHEMA_VERSION,
    "status": "pass",
    "german_record_count": 520,
    "reverse_record_count": 1046,
    "reverse_counts": {"el-en": 256, "pl-en": 264, "sv-en": 261, "uk-en": 265},
    "minimum_250_each": True,
    "source_mapping_complete": True,
    "source_script_preservation": True,
    "original_script_preserved_count": 1046,
    "limitations": (
        "All data are mechanically derived from already shipped pair modules; no new translations were created.",
        "No native-speaker review has occurred; register and grammar heuristics retain explicit reviewer state.",
        "Legacy pronunciation strings are preserved as hints and are not renamed transliterations.",
    ),
}

REVERSE_SPECS = (
    ("en-pl", "pl-en", "Polish", "pl-PL", "Latin", "Polski", "🇵🇱"),
    ("en-uk", "uk-en", "Ukrainian", "uk-UA", "Cyrillic", "Українська", "🇺🇦"),
    ("en-sv", "sv-en", "Swedish", "sv-SE", "Latin", "Svenska", "🇸🇪"),
    ("en-el", "el-en", "Greek", "el-GR", "Greek", "Ελληνικά", "🇬🇷"),
)

# Exact, conservative one-word lemmas from the existing German target/source
# text.  An absent entry means unknown, not a guessed article or gender.
GERMAN_NOUNS = {
    "Mutter": ("die", "feminine"), "Vater": ("der", "masculine"), "Schwester": ("die", "feminine"), "Bruder": ("der", "masculine"),
    "Tochter": ("die", "feminine"), "Sohn": ("der", "masculine"), "Großmutter": ("die", "feminine"), "Großvater": ("der", "masculine"),
    "Onkel": ("der", "masculine"), "Tante": ("die", "feminine"), "Familie": ("die", "feminine"), "Brot": ("das", "neuter"),
    "Reis": ("der", "masculine"), "Käse": ("der", "masculine"), "Ei": ("das", "neuter"), "Fleisch": ("das", "neuter"),
    "Huhn": ("das", "neuter"), "Fisch": ("der", "masculine"), "Apfel": ("der", "masculine"), "Banane": ("die", "feminine"),
    "Salat": ("der", "masculine"), "Suppe": ("die", "feminine"), "Zucker": ("der", "masculine"), "Salz": ("das", "neuter"),
    "Butter": ("die", "feminine"), "Kuchen": ("der", "masculine"), "Wasser": ("das", "neuter"), "Tee": ("der", "masculine"),
    "Kaffee": ("der", "masculine"), "Milch": ("die", "feminine"), "Saft": ("der", "masculine"), "Bier": ("das", "neuter"),
    "Wein": ("der", "masculine"), "Limonade": ("die", "feminine"), "Kopf": ("der", "masculine"), "Auge": ("das", "neuter"),
    "Ohr": ("das", "neuter"), "Nase": ("die", "feminine"), "Mund": ("der", "masculine"), "Hand": ("die", "feminine"),
    "Fuß": ("der", "masculine"), "Bein": ("das", "neuter"), "Arm": ("der", "masculine"), "Herz": ("das", "neuter"),
    "Haar": ("das", "neuter"), "Zahn": ("der", "masculine"), "Sonne": ("die", "feminine"), "Regen": ("der", "masculine"),
    "Schnee": ("der", "masculine"), "Wind": ("der", "masculine"), "Wolke": ("die", "feminine"), "Sturm": ("der", "masculine"),
    "Hund": ("der", "masculine"), "Katze": ("die", "feminine"), "Vogel": ("der", "masculine"), "Pferd": ("das", "neuter"),
    "Kuh": ("die", "feminine"), "Schwein": ("das", "neuter"), "Schaf": ("das", "neuter"), "Maus": ("die", "feminine"),
    "Bär": ("der", "masculine"), "Löwe": ("der", "masculine"), "Tiger": ("der", "masculine"), "Elefant": ("der", "masculine"),
}
FUNCTION_WORDS = frozenset("ich du er sie es wir ihr man das der die den dem ein eine einen einem und oder nicht zu in im am an auf mit für von".split())


def _canonical(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(_canonical(part) for part in parts).encode("utf-8")).hexdigest()[:24]


def _stage(entry: PhraseEntry) -> str:
    if entry.category == "script":
        return "beginner_script"
    if entry.subcategory in {"numbers", "days", "months", "time"}:
        return "beginner_foundations"
    if entry.subcategory in {"greeting", "courtesy", "introduction"}:
        return "beginner_social"
    if entry.subcategory in {"shopping", "restaurant", "transit", "emergency"}:
        return "beginner_practical"
    if entry.category == "sentence" or entry.subcategory in {"question", "need", "opinion", "small_talk"}:
        return "beginner_sentences"
    return "beginner_core"


def _source_ref(pair_id: str, index: int, entry: PhraseEntry) -> dict[str, Any]:
    module = Path(__file__).with_name("pair_" + pair_id.replace("-", "_") + ".py")
    digest = _digest(pair_id, entry.source, entry.target, entry.category, entry.subcategory)
    return {
        "repository": "Amal-David/polyglot", "source_pair_id": pair_id,
        "source_module": "polyglot/data/" + module.name,
        "source_module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "source_entry_index": index, "origin_content_id": f"origin-v1:{pair_id}:{digest}",
        "origin_content_digest": digest, "translation_status": "derived_only_no_new_translation",
        "reviewer_state": "not_native_reviewed",
    }


def _register(entry: PhraseEntry) -> dict[str, str]:
    if entry.subcategory == "courtesy":
        return {"value": "courtesy_context", "evidence": "source_subcategory", "review_status": "not_native_reviewed"}
    return {"value": "unknown", "evidence": "not_encoded_in_source_data", "review_status": "not_native_reviewed"}


def _word_order(text: str, category: str) -> dict[str, str]:
    if category not in {"phrase", "sentence"}:
        return {"pattern": "not_applicable", "evidence": "not_a_multiword_prompt"}
    lowered = _canonical(text)
    if lowered.startswith(("wo ", "was ", "wann ", "warum ", "wie ", "wer ", "welch")):
        return {"pattern": "wh_question_finite_verb_second", "evidence": "surface_heuristic", "review_status": "not_native_reviewed"}
    if lowered.startswith(("kann", "können", "hast", "haben", "ist", "sind", "darf", "dürfen", "möchtest", "möchten", "willst", "wollen")):
        return {"pattern": "yes_no_question_finite_verb_initial", "evidence": "surface_heuristic", "review_status": "not_native_reviewed"}
    if lowered.startswith(("ich ", "du ", "er ", "sie ", "es ", "wir ", "ihr ", "man ", "das ")):
        return {"pattern": "main_clause_finite_verb_second", "evidence": "surface_heuristic", "review_status": "not_native_reviewed"}
    return {"pattern": "unannotated", "evidence": "no_safe_automatic_rule"}


def _cloze(text: str, category: str) -> dict[str, str] | None:
    if category not in {"phrase", "sentence"}:
        return None
    tokens = list(re.finditer(r"[A-Za-zÄÖÜäöüß]+", text))
    candidates = [item for item in tokens if _canonical(item.group()) not in FUNCTION_WORDS]
    if len(tokens) < 3 or not candidates:
        return None
    chosen = candidates[len(candidates) // 2]
    return {"prompt_text": text[:chosen.start()] + "_____" + text[chosen.end():], "answer_text": chosen.group(), "answer_source": "exact_substring_of_original_german_text", "generation_rule": "deterministic_middle_content_token", "review_status": "automated_staging_only"}


def annotate_german_pair(pair: LanguagePair) -> LanguagePair:
    """Attach first-class-path metadata without changing any existing card text."""
    if pair.id not in {"en-de", "de-en"}:
        raise ValueError(f"not a German pair: {pair.id}")
    direction = "production_to_german" if pair.id == "en-de" else "comprehension_from_german"
    entries: list[PhraseEntry] = []
    for index, entry in enumerate(pair.phrases):
        german_text = entry.target if pair.id == "en-de" else entry.source
        content_digest = _digest(pair.id, entry.source, entry.target, entry.category, entry.subcategory)
        noun = GERMAN_NOUNS.get(german_text)
        tags = (["script"] if entry.category == "script" else [])
        if entry.category == "vocab" and entry.subcategory != "adjectives": tags.append("lexical_item")
        if entry.category in {"phrase", "sentence"}: tags.append("multiword_context")
        if noun: tags.append("noun_article_gender_available")
        metadata = {
            "schema_version": SCHEMA_VERSION, "record_id": f"german-path-v1:{pair.id}:{content_digest}",
            "learning_path": "german_first_class_v1", "direction": direction,
            "source_locale": "en-US" if pair.id == "en-de" else "de-DE",
            "target_locale": "de-DE" if pair.id == "en-de" else "en-US",
            "source_script": "Latin", "target_script": "Latin", "original_script_preserved": True,
            "learning_stage": _stage(entry), "topic": entry.subcategory, "register": _register(entry),
            "grammar_tags": tags, "word_order": _word_order(german_text, entry.category),
            "production_prompt": {"mode": "typed_recall", "prompt_side": "source_text", "answer_side": "target_text", "answer_status": "existing_shipped_translation"},
            "cloze": _cloze(german_text, entry.category),
            "legacy_pronunciation_status": "preserved_verbatim_not_reclassified_as_transliteration",
            "provenance": _source_ref(pair.id, index, entry), "reviewer_state": "not_native_reviewed",
        }
        if noun:
            metadata["article_gender"] = {"article": noun[0], "gender": noun[1], "evidence": "exact_conservative_lemma_match", "review_status": "not_native_reviewed"}
        entries.append(replace(entry, metadata=metadata))
    return replace(pair, phrases=tuple(entries))


def reverse_pair(source_pair: LanguagePair, *, pair_id: str, language: str, locale: str, script: str, native: str, flag: str) -> LanguagePair:
    """Create a registered reverse direction from exact shipped records only."""
    entries: list[PhraseEntry] = []
    for index, entry in enumerate(source_pair.phrases):
        digest = _digest(source_pair.id, entry.source, entry.target, entry.category, entry.subcategory)
        metadata = {
            "schema_version": SCHEMA_VERSION, "record_id": f"reverse-v1:{pair_id}:{digest}", "derived_pair_id": pair_id,
            "source_locale": locale, "target_locale": "en-US", "source_script": script, "target_script": "Latin",
            "original_script_preserved": True, "learning_stage": _stage(entry), "topic": entry.subcategory,
            "register": _register(entry), "transliteration": None,
            "transliteration_status": "not_created_by_staging_original_script_retained",
            "pronunciation_status": "legacy_hint_not_pronunciation_for_reverse_direction",
            "provenance": _source_ref(source_pair.id, index, entry), "reviewer_state": "not_native_reviewed",
        }
        entries.append(PhraseEntry(source=entry.target, target=entry.source, pronunciation=entry.pronunciation, category=entry.category, subcategory=entry.subcategory, note=entry.note, metadata=metadata))
    return LanguagePair(id=pair_id, source_lang=language, target_lang="English", source_code=pair_id.split("-")[0], target_code="en", target_native="English", script=script, flag=flag, blurb=f"Evidence-informed {language} → English direction, mechanically reversed from existing shipped records.", phrases=tuple(entries))


def build_reverse_pairs(pairs: Iterable[LanguagePair]) -> tuple[LanguagePair, ...]:
    by_id = {pair.id: pair for pair in pairs}
    return tuple(reverse_pair(by_id[source], pair_id=derived, language=language, locale=locale, script=script, native=native, flag=flag) for source, derived, language, locale, script, native, flag in REVERSE_SPECS)


def validate_v2_content(pairs: Iterable[LanguagePair]) -> dict[str, Any]:
    """Return deterministic release-gate facts without touching learner state."""
    by_id = {pair.id: pair for pair in pairs}
    german = [entry for pair_id in ("en-de", "de-en") for entry in by_id[pair_id].phrases]
    reverse = [entry for _, pair_id, *_ in REVERSE_SPECS for entry in by_id[pair_id].phrases]
    reverse_counts = {pair_id: len(by_id[pair_id].phrases) for _, pair_id, *_ in REVERSE_SPECS}
    metadata = [entry.metadata for entry in german + reverse]
    record_ids = [str(item.get("record_id", "")) for item in metadata]
    script_by_pair = {pair_id: script for _, pair_id, _, _, script, _, _ in REVERSE_SPECS}
    return {
        "direction_count": len(by_id), "entry_count": sum(len(pair.phrases) for pair in by_id.values()),
        "german_record_count": len(german), "reverse_record_count": len(reverse), "reverse_counts": reverse_counts,
        "minimum_250_each": all(count >= 250 for count in reverse_counts.values()),
        "unique_record_ids": len(record_ids) == len(set(record_ids)) and all(record_ids),
        "original_script_preserved": all(entry.metadata.get("original_script_preserved") is True for entry in reverse),
        "reverse_scripts": {pair_id: by_id[pair_id].script == script_by_pair[pair_id] for pair_id in script_by_pair},
        "not_native_reviewed": all(entry.metadata.get("reviewer_state") == "not_native_reviewed" for entry in german + reverse),
        "german_article_gender_coverage": sum(1 for entry in german if entry.metadata.get("article_gender")),
        "german_cloze_coverage": sum(1 for entry in german if entry.metadata.get("cloze")),
    }
