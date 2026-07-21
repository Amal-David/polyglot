"""Private SQLite state for explicit Polyglot learning reviews.

This module is intentionally separate from the fail-soft JSON used by old
ambient hooks.  A review either commits atomically or reports the real error;
it never silently drops a learner grade.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import sqlite3
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from polyglot.platform import atomic_write_text
from polyglot.scheduler import MAX_INTERVAL_SECONDS, ScheduleState, VALID_GRADES, schedule

SCHEMA_VERSION = 1
MAX_HISTORY = 2_000
MAX_IMPORT_BYTES = 4 * 1024 * 1024
VALID_DIRECTIONS = frozenset(("forward", "reverse", "cloze"))
VALID_MODES = frozenset(("production", "recognition", "forward", "reverse", "cloze"))
MAX_COUNTER_VALUE = 1_000_000
MAX_PREFERENCES = 1_000


def _local_day_start(timestamp: float) -> float:
    """Return the learner machine's local midnight, including DST rules."""
    local = time.localtime(timestamp)
    return time.mktime(
        (local.tm_year, local.tm_mon, local.tm_mday, 0, 0, 0, 0, 0, -1)
    )


class LearnerStateError(RuntimeError):
    """Raised when durable learner state cannot safely be used."""


def _private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        path.chmod(0o700)
    return path


def _chmod_private_file_if_present(path: Path) -> None:
    """Restrict a SQLite file while tolerating transient sidecar removal."""
    try:
        path.chmod(0o600)
    except FileNotFoundError:
        # SQLite may remove -wal/-shm between close() and chmod().
        pass


class LearnerStore:
    """A small concurrent-safe SQLite store scoped to one product data dir."""

    def __init__(self, root: Path):
        self.root = _private_directory(Path(root))
        self.path = self.root / "learning.sqlite3"
        self.notice_path = self.root / ".quarantine-notice"
        self.was_quarantined = False
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as error:
            raise LearnerStateError(f"unable to open learner state: {error}") from error

    @contextmanager
    def _session(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()
            if os.name != "nt":
                for path in (self.path, self.path.with_name(self.path.name + "-wal"), self.path.with_name(self.path.name + "-shm")):
                    _chmod_private_file_if_present(path)

    def _initialize(self) -> None:
        try:
            with self._session() as connection:
                connection.execute("PRAGMA journal_mode = WAL")
                version = int(connection.execute("PRAGMA user_version").fetchone()[0])
                if version > SCHEMA_VERSION:
                    raise sqlite3.DatabaseError("learner state was created by a newer Polyglot")
                if version == 0:
                    connection.executescript(
                        """
                        CREATE TABLE IF NOT EXISTS card_state (
                          pair_id TEXT NOT NULL,
                          card_id TEXT NOT NULL,
                          direction TEXT NOT NULL,
                          due_at REAL NOT NULL,
                          interval_seconds INTEGER NOT NULL,
                          repetitions INTEGER NOT NULL,
                          lapses INTEGER NOT NULL,
                          last_grade TEXT,
                          last_seen_at REAL,
                          difficulty REAL NOT NULL,
                          mode TEXT NOT NULL,
                          PRIMARY KEY (pair_id, card_id, direction)
                        );
                        CREATE INDEX IF NOT EXISTS card_state_due
                          ON card_state(pair_id, direction, due_at, card_id);
                        CREATE TABLE IF NOT EXISTS review_history (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          pair_id TEXT NOT NULL,
                          card_id TEXT NOT NULL,
                          direction TEXT NOT NULL,
                          graded_at REAL NOT NULL,
                          grade TEXT NOT NULL,
                          interval_seconds INTEGER NOT NULL,
                          lapses INTEGER NOT NULL
                        );
                        CREATE INDEX IF NOT EXISTS review_history_pair_time
                          ON review_history(pair_id, graded_at);
                        CREATE TABLE IF NOT EXISTS preferences (
                          pair_id TEXT PRIMARY KEY,
                          daily_goal INTEGER NOT NULL DEFAULT 5
                        );
                        """
                    )
                    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            if self.path.exists() and os.name != "nt":
                self.path.chmod(0o600)
        except sqlite3.DatabaseError as error:
            self._quarantine(error)

    def _quarantine(self, error: Exception) -> None:
        if not self.path.exists():
            raise LearnerStateError(f"invalid learner state: {error}") from error
        stamp = str(time.time_ns())
        target = self.path.with_name(f"learning.sqlite3.corrupt-{stamp}")
        try:
            shutil.move(str(self.path), str(target))
            for suffix in ("-wal", "-shm"):
                sidecar = self.path.with_name(self.path.name + suffix)
                if sidecar.exists():
                    shutil.move(str(sidecar), str(target) + suffix)
        except OSError as move_error:
            raise LearnerStateError(f"cannot quarantine corrupt learner state: {move_error}") from move_error
        self.was_quarantined = True
        atomic_write_text(self.notice_path, "quarantined\n")
        self._initialize()

    def consume_quarantine_notice(self) -> bool:
        """Consume the one human-facing recovery notice for this corruption."""
        try:
            self.notice_path.unlink()
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def _row_to_state(row: sqlite3.Row | None) -> ScheduleState | None:
        if row is None:
            return None
        return ScheduleState(
            due_at=float(row["due_at"]), interval_seconds=int(row["interval_seconds"]),
            repetitions=int(row["repetitions"]), lapses=int(row["lapses"]),
            last_grade=row["last_grade"], last_seen_at=row["last_seen_at"],
            difficulty=float(row["difficulty"]), mode=str(row["mode"]),
        )

    def get_state(self, pair_id: str, card_id: str, direction: str) -> ScheduleState | None:
        with self._session() as connection:
            row = connection.execute(
                "SELECT * FROM card_state WHERE pair_id = ? AND card_id = ? AND direction = ?",
                (pair_id, card_id, direction),
            ).fetchone()
        return self._row_to_state(row)

    def due_card_ids(self, pair_id: str, direction: str, now: float, *, limit: int = 200) -> list[str]:
        with self._session() as connection:
            rows = connection.execute(
                "SELECT card_id FROM card_state WHERE pair_id = ? AND direction = ? AND due_at <= ? "
                "ORDER BY due_at, card_id LIMIT ?", (pair_id, direction, now, limit),
            ).fetchall()
        return [str(row["card_id"]) for row in rows]

    def known_card_ids(self, pair_id: str, direction: str) -> set[str]:
        with self._session() as connection:
            rows = connection.execute(
                "SELECT card_id FROM card_state WHERE pair_id = ? AND direction = ?", (pair_id, direction)
            ).fetchall()
        return {str(row["card_id"]) for row in rows}

    def record_grade(self, pair_id: str, card_id: str, direction: str, grade: str, now: float, *, mode: str = "production") -> ScheduleState:
        if direction not in VALID_DIRECTIONS or grade not in VALID_GRADES:
            raise ValueError("invalid review direction or grade")
        with self._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                old = self._row_to_state(connection.execute(
                    "SELECT * FROM card_state WHERE pair_id = ? AND card_id = ? AND direction = ?",
                    (pair_id, card_id, direction),
                ).fetchone())
                updated = schedule(old, grade, now)
                updated = ScheduleState(**{**asdict(updated), "mode": mode})
                connection.execute(
                    """INSERT INTO card_state (pair_id, card_id, direction, due_at, interval_seconds,
                       repetitions, lapses, last_grade, last_seen_at, difficulty, mode)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(pair_id, card_id, direction) DO UPDATE SET
                       due_at=excluded.due_at, interval_seconds=excluded.interval_seconds,
                       repetitions=excluded.repetitions, lapses=excluded.lapses,
                       last_grade=excluded.last_grade, last_seen_at=excluded.last_seen_at,
                       difficulty=excluded.difficulty, mode=excluded.mode""",
                    (pair_id, card_id, direction, updated.due_at, updated.interval_seconds,
                     updated.repetitions, updated.lapses, updated.last_grade, updated.last_seen_at,
                     updated.difficulty, updated.mode),
                )
                connection.execute(
                    "INSERT INTO review_history (pair_id, card_id, direction, graded_at, grade, interval_seconds, lapses) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (pair_id, card_id, direction, now, grade, updated.interval_seconds, updated.lapses),
                )
                connection.execute(
                    "DELETE FROM review_history WHERE id NOT IN (SELECT id FROM review_history ORDER BY id DESC LIMIT ?)",
                    (MAX_HISTORY,),
                )
                connection.execute("COMMIT")
                return updated
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def progress(self, pair_id: str | None, now: float) -> dict[str, int]:
        where = " WHERE pair_id = ?" if pair_id else ""
        values: tuple[object, ...] = (pair_id,) if pair_id else ()
        with self._session() as connection:
            total = int(connection.execute(f"SELECT COUNT(*) FROM card_state{where}", values).fetchone()[0])
            due = int(connection.execute(f"SELECT COUNT(*) FROM card_state{where}{' AND' if where else ' WHERE'} due_at <= ?", (*values, now)).fetchone()[0])
            learned = int(connection.execute(f"SELECT COUNT(*) FROM card_state{where}{' AND' if where else ' WHERE'} repetitions > 0", values).fetchone()[0])
            today = _local_day_start(now)
            reviewed_today = int(connection.execute(
                f"SELECT COUNT(*) FROM review_history{where}{' AND' if where else ' WHERE'} graded_at >= ?", (*values, today)
            ).fetchone()[0])
        return {"tracked": total, "due": due, "learning": learned, "reviewed_today": reviewed_today}

    def get_goal(self, pair_id: str) -> int:
        with self._session() as connection:
            row = connection.execute("SELECT daily_goal FROM preferences WHERE pair_id = ?", (pair_id,)).fetchone()
        return int(row["daily_goal"]) if row else 5

    def set_goal(self, pair_id: str, daily_goal: int) -> int:
        if not 1 <= daily_goal <= 100:
            raise ValueError("daily goal must be between 1 and 100")
        with self._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("INSERT INTO preferences(pair_id, daily_goal) VALUES (?, ?) ON CONFLICT(pair_id) DO UPDATE SET daily_goal=excluded.daily_goal", (pair_id, daily_goal))
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return daily_goal

    def forget(self, pair_id: str | None = None) -> int:
        with self._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                if pair_id:
                    count = int(connection.execute("SELECT COUNT(*) FROM card_state WHERE pair_id = ?", (pair_id,)).fetchone()[0])
                    connection.execute("DELETE FROM card_state WHERE pair_id = ?", (pair_id,))
                    connection.execute("DELETE FROM review_history WHERE pair_id = ?", (pair_id,))
                    connection.execute("DELETE FROM preferences WHERE pair_id = ?", (pair_id,))
                else:
                    count = int(connection.execute("SELECT COUNT(*) FROM card_state").fetchone()[0])
                    connection.execute("DELETE FROM card_state")
                    connection.execute("DELETE FROM review_history")
                    connection.execute("DELETE FROM preferences")
                connection.execute("COMMIT")
                return count
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def export_data(self) -> dict[str, Any]:
        with self._session() as connection:
            states = [dict(row) for row in connection.execute("SELECT * FROM card_state ORDER BY pair_id, card_id, direction")]
            preferences = [dict(row) for row in connection.execute("SELECT * FROM preferences ORDER BY pair_id")]
        return {"schema_version": SCHEMA_VERSION, "card_state": states, "preferences": preferences}

    def import_data(self, payload: dict[str, Any], known_cards: dict[str, set[str]]) -> int:
        if (
            not isinstance(payload, dict)
            or type(payload.get("schema_version")) is not int
            or payload["schema_version"] != SCHEMA_VERSION
        ):
            raise ValueError("unsupported learner export")
        states = payload.get("card_state")
        preferences = payload.get("preferences", [])
        if (
            not isinstance(states, list)
            or not isinstance(preferences, list)
            or len(states) > 100_000
            or len(preferences) > MAX_PREFERENCES
        ):
            raise ValueError("invalid learner export")
        validated: list[tuple[Any, ...]] = []
        for row in states:
            if not isinstance(row, dict):
                raise ValueError("invalid card state")
            pair_id, card_id, direction = row.get("pair_id"), row.get("card_id"), row.get("direction")
            if (
                not isinstance(pair_id, str)
                or not isinstance(card_id, str)
                or card_id not in known_cards.get(pair_id, set())
                or not isinstance(direction, str)
                or direction not in VALID_DIRECTIONS
            ):
                raise ValueError("export contains an unknown card or direction")
            grade = row.get("last_grade")
            if grade is not None and (
                not isinstance(grade, str) or grade not in VALID_GRADES
            ):
                raise ValueError("invalid grade in learner export")
            try:
                raw_due_at = row["due_at"]
                raw_interval = row["interval_seconds"]
                raw_repetitions = row["repetitions"]
                raw_lapses = row["lapses"]
            except KeyError as error:
                raise ValueError("invalid card state") from error
            raw_last_seen = row.get("last_seen_at")
            raw_difficulty = row.get("difficulty", 5.0)
            mode = row.get("mode", "production")
            if (
                type(raw_due_at) not in (int, float)
                or type(raw_interval) is not int
                or type(raw_repetitions) is not int
                or type(raw_lapses) is not int
                or (raw_last_seen is not None and type(raw_last_seen) not in (int, float))
                or type(raw_difficulty) not in (int, float)
            ):
                raise ValueError("invalid card state")
            due_at = float(raw_due_at)
            interval = raw_interval
            repetitions = raw_repetitions
            lapses = raw_lapses
            last_seen_at = None if raw_last_seen is None else float(raw_last_seen)
            difficulty = float(raw_difficulty)
            if (
                not math.isfinite(due_at)
                or due_at < 0
                or not 0 <= interval <= MAX_INTERVAL_SECONDS
                or not 0 <= repetitions <= MAX_COUNTER_VALUE
                or not 0 <= lapses <= MAX_COUNTER_VALUE
                or (last_seen_at is not None and (not math.isfinite(last_seen_at) or last_seen_at < 0))
                or not math.isfinite(difficulty)
                or not 1.0 <= difficulty <= 10.0
                or not isinstance(mode, str)
                or mode not in VALID_MODES
            ):
                raise ValueError("invalid card state")
            validated.append(
                (
                    pair_id,
                    card_id,
                    direction,
                    due_at,
                    interval,
                    repetitions,
                    lapses,
                    grade,
                    last_seen_at,
                    difficulty,
                    mode,
                )
            )
        validated_preferences: list[tuple[str, int]] = []
        for pref in preferences:
            if not isinstance(pref, dict) or not isinstance(pref.get("pair_id"), str):
                raise ValueError("invalid learner preference")
            pair_id = pref["pair_id"]
            if pair_id not in known_cards:
                raise ValueError("invalid learner preference")
            daily_goal = pref.get("daily_goal", 5)
            if type(daily_goal) is not int:
                raise ValueError("invalid learner preference")
            if not 1 <= daily_goal <= 100:
                raise ValueError("invalid learner preference")
            validated_preferences.append((pair_id, daily_goal))
        with self._session() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                for row in validated:
                    connection.execute(
                        """INSERT INTO card_state VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(pair_id, card_id, direction) DO UPDATE SET
                        due_at=excluded.due_at, interval_seconds=excluded.interval_seconds,
                        repetitions=excluded.repetitions, lapses=excluded.lapses,
                        last_grade=excluded.last_grade, last_seen_at=excluded.last_seen_at,
                        difficulty=excluded.difficulty, mode=excluded.mode""", row)
                for pair_id, daily_goal in validated_preferences:
                    connection.execute(
                        "INSERT INTO preferences(pair_id, daily_goal) VALUES (?, ?) "
                        "ON CONFLICT(pair_id) DO UPDATE SET daily_goal=excluded.daily_goal",
                        (pair_id, daily_goal),
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return len(validated)


def write_export(path: Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    if len(raw.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise ValueError("learner export exceeds the size limit")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        if os.name != "nt":
            target.chmod(0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def read_export(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    if len(raw) > MAX_IMPORT_BYTES:
        raise ValueError("learner export exceeds the size limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid learner export") from error
    if not isinstance(payload, dict):
        raise ValueError("invalid learner export")
    return payload
