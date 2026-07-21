"""Deterministic, local-only scheduling for explicit Polyglot reviews.

The scheduler intentionally has no database or clock dependency.  That keeps
the learning rules inspectable and makes a recorded review sequence replayable
in tests and after a restart.
"""

from __future__ import annotations

from dataclasses import dataclass

DAY_SECONDS = 24 * 60 * 60
AGAIN_SECONDS = 10 * 60
MAX_INTERVAL_SECONDS = 180 * DAY_SECONDS
VALID_GRADES = frozenset(("again", "hard", "good", "easy"))


@dataclass(frozen=True)
class ScheduleState:
    """The persisted scheduling fields for one card and one direction."""

    due_at: float
    interval_seconds: int = 0
    repetitions: int = 0
    lapses: int = 0
    last_grade: str | None = None
    last_seen_at: float | None = None
    difficulty: float = 5.0
    mode: str = "production"


def schedule(previous: ScheduleState | None, grade: str, now: float) -> ScheduleState:
    """Return the next state for an explicit grade at ``now``.

    ``again`` is due in exactly ten minutes.  ``hard``, ``good``, and ``easy``
    follow the public, deliberately simple multipliers.  A new card is any
    card with no prior state or a zero prior interval.
    """
    if grade not in VALID_GRADES:
        raise ValueError(f"unknown grade: {grade}")

    old = previous or ScheduleState(due_at=now)
    prior = max(0, int(old.interval_seconds))
    is_new = prior == 0
    difficulty = min(10.0, max(1.0, old.difficulty + {"again": 0.4, "hard": 0.15, "good": -0.1, "easy": -0.25}[grade]))

    if grade == "again":
        interval = AGAIN_SECONDS
        repetitions = 0
        lapses = old.lapses + 1
    elif grade == "hard":
        interval = max(DAY_SECONDS, int(round(prior * 1.2)))
        repetitions = old.repetitions + 1
        lapses = old.lapses
    elif grade == "good":
        interval = DAY_SECONDS if is_new else int(round(prior * 2.5))
        repetitions = old.repetitions + 1
        lapses = old.lapses
    else:
        interval = 4 * DAY_SECONDS if is_new else int(round(prior * 4.0))
        repetitions = old.repetitions + 1
        lapses = old.lapses

    interval = min(MAX_INTERVAL_SECONDS, max(AGAIN_SECONDS, interval))
    return ScheduleState(
        due_at=now + interval,
        interval_seconds=interval,
        repetitions=repetitions,
        lapses=lapses,
        last_grade=grade,
        last_seen_at=now,
        difficulty=difficulty,
        mode=old.mode,
    )
