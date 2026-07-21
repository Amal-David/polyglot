"""Small, dependency-free safety boundary for host-visible learning content."""

from __future__ import annotations

import re
import unicodedata


AMBIENT_MAX_CHARACTERS = 180
AMBIENT_MAX_TOKENS = 80
_SECRET_OR_CONTEXT = re.compile(
    r"(?:__[^\s]*(?:secret|token|prompt|transcript|tool)[^\s]*__|"
    r"(?:api[_ -]?key|authorization|bearer|password|secret(?:[_ -]?(?:key|token|value|sentinel))?)\s*[:=]|"
    r"(?:^|\s)/(?:Users|home|private|tmp)/|(?:^|\s)[A-Za-z]:\\|~/)",
    re.IGNORECASE,
)


def contains_control_or_sensitive_data(value: str) -> bool:
    """Reject controls and values resembling host context or credentials."""
    if not isinstance(value, str) or _SECRET_OR_CONTEXT.search(value):
        return True
    return any(unicodedata.category(character) == "Cc" for character in value)


def approximate_token_count(value: str) -> int:
    """Conservative tokenizer-free approximation, including one CJK rune/token."""
    return len(re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", value))


def _safe_learning_line(kind: str, prompt: str, answer: str) -> str | None:
    if contains_control_or_sensitive_data(prompt) or contains_control_or_sensitive_data(answer):
        return None
    line = f"Polyglot {kind} · {prompt} → {answer}"
    if len(line) > AMBIENT_MAX_CHARACTERS or approximate_token_count(line) > AMBIENT_MAX_TOKENS:
        return None
    return line


def safe_ambient_line(prompt: str, answer: str) -> str | None:
    """Return a bounded inert due-card payload, or fail closed."""
    return _safe_learning_line("due", prompt, answer)


def safe_starter_line(prompt: str, answer: str) -> str | None:
    """Return a bounded, explicitly ungraded first-exposure payload."""
    return _safe_learning_line("starter", prompt, answer)


def is_safe_ambient_message(value: object) -> bool:
    """Validate host output even when a wrapper or child supplied the text."""
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not contains_control_or_sensitive_data(value)
        and len(value) <= AMBIENT_MAX_CHARACTERS
        and approximate_token_count(value) <= AMBIENT_MAX_TOKENS
    )
