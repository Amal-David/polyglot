"""Review-card construction and compact terminal rendering.

No learner state is mutated here.  Selection receives an explicit clock so it
can be replayed identically in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from polyglot.data.pairs import LanguagePair, PhraseEntry, stable_card_id
from polyglot.learning_store import LearnerStore
from polyglot.safety import safe_ambient_line, safe_starter_line

DEFAULT_SESSION_SIZE = 5
LEARNING_STAGE_ORDER = (
    "beginner_social",
    "beginner_foundations",
    "beginner_core",
    "beginner_practical",
    "beginner_sentences",
    "beginner_script",
)
_SCRIPT_FIRST_STAGE_ORDER = (
    "beginner_script",
    *(
        stage
        for stage in LEARNING_STAGE_ORDER
        if stage != "beginner_script"
    ),
)
_CARD_INDEX_CACHE: dict[
    tuple[str, str, int, int], tuple[dict[str, "ReviewCard"], tuple[str, ...]]
] = {}


@dataclass(frozen=True)
class ReviewCard:
    pair_id: str
    card_id: str
    direction: str
    prompt: str
    answer: str
    hint: str
    mode: str


def _card(pair: LanguagePair, entry: PhraseEntry, direction: str) -> ReviewCard:
    card_id = stable_card_id(pair.id, entry)
    metadata = entry.metadata
    if direction == "reverse":
        prompt, answer = entry.target, entry.source
        hint = "" if metadata.get("pronunciation_status") else entry.pronunciation
    elif direction == "cloze":
        cloze = metadata.get("cloze")
        if isinstance(cloze, dict) and cloze.get("prompt_text") and cloze.get("answer_text"):
            prompt, answer = f"Complete: {cloze['prompt_text']}", cloze["answer_text"]
            hint = "German contextual cloze · automated staging only"
        else:
            prompt, answer = f"Complete: {entry.source}", entry.target
            hint = entry.note
    else:
        prompt, answer = entry.source, entry.target
        hint = entry.pronunciation
    return ReviewCard(pair.id, card_id, direction, prompt, answer, hint, direction)


def _card_index(
    pair: LanguagePair, direction: str
) -> tuple[dict[str, ReviewCard], tuple[str, ...]]:
    """Cache immutable card rendering for the active shipped pair."""
    key = (pair.id, direction, id(pair.phrases), len(pair.phrases))
    cached = _CARD_INDEX_CACHE.get(key)
    if cached is None:
        stage_order = (
            LEARNING_STAGE_ORDER
            if pair.script.casefold() == "latin"
            else _SCRIPT_FIRST_STAGE_ORDER
        )
        stage_rank = {
            stage: index for index, stage in enumerate(stage_order)
        }
        cards: dict[str, ReviewCard] = {}
        ordered_entries = sorted(
            enumerate(pair.phrases),
            key=lambda item: (
                stage_rank.get(
                    str(item[1].metadata.get("learning_stage", "")),
                    len(stage_order),
                ),
                item[0],
            ),
        )
        ordered_ids: list[str] = []
        for _catalog_index, entry in ordered_entries:
            card = _card(pair, entry, direction)
            cards[card.card_id] = card
            ordered_ids.append(card.card_id)
        cached = (cards, tuple(ordered_ids))
        _CARD_INDEX_CACHE.clear()
        _CARD_INDEX_CACHE[key] = cached
    return cached


def build_review_session(
    store: LearnerStore,
    pair: LanguagePair,
    direction: str,
    now: float,
    *,
    limit: int = DEFAULT_SESSION_SIZE,
) -> list[ReviewCard]:
    """Build a deterministic, no-repeat blend of due then new cards."""
    if limit < 1:
        raise ValueError("review count must be at least one")
    cards, ordered_ids = _card_index(pair, direction)
    due_ids = [card_id for card_id in store.due_card_ids(pair.id, direction, now, limit=limit * 4) if card_id in cards]
    known = store.known_card_ids(pair.id, direction)
    new_ids = [card_id for card_id in ordered_ids if card_id not in known]

    due_target = min(len(due_ids), max(1, round(limit * 0.8)))
    selected = due_ids[:due_target]
    selected_set = set(selected)
    # Fill remaining spots with unseen cards first, then due cards only when
    # there are no unseen candidates.  The set guards a duplicate regardless.
    for pool in (new_ids, due_ids):
        for card_id in pool:
            if len(selected) >= limit:
                break
            if card_id not in selected_set:
                selected.append(card_id)
                selected_set.add(card_id)
    return [cards[card_id] for card_id in selected[:limit]]


def due_ambient_card(store: LearnerStore, pair: LanguagePair, now: float) -> ReviewCard | None:
    """Return one due production card without introducing or updating it."""
    by_id, _ordered_ids = _card_index(pair, "forward")
    for card_id in store.due_card_ids(pair.id, "forward", now, limit=1):
        if card_id in by_id:
            return by_id[card_id]
    return None


def starter_ambient_card(pair: LanguagePair) -> ReviewCard | None:
    """Return the first staged safe card without introducing learner state."""
    by_id, ordered_ids = _card_index(pair, "forward")
    for card_id in ordered_ids:
        card = by_id[card_id]
        if safe_starter_line(card.prompt, card.answer):
            return card
    return None


def compact_ambient_line(card: ReviewCard) -> str | None:
    """Render one inert due-card line inside the shared ambient budget."""
    return safe_ambient_line(card.prompt, card.answer)


def compact_starter_line(card: ReviewCard) -> str | None:
    """Render one inert starter exposure inside the shared ambient budget."""
    return safe_starter_line(card.prompt, card.answer)
