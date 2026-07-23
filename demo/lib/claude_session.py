#!/usr/bin/env python3
"""Staged agent-session replay for the VHS launch recording.

Prints a Claude Code-style transcript at reading pace, then calls the
bundled Stop hook exactly once at the end of the turn — matching Polyglot's
real hook contract (hooks/hooks.json registers a Stop hook, not a
PostToolUse hook). The tool calls on screen are scripted for pacing; the
phrase card is genuine bundled hook output.

Usage: claude_session.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_SCRIPT = REPO_ROOT / "scripts" / "ambient.py"

DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
RESET = "\033[0m"

PROMPT = "wire up the webhook signature check"
CALLS = [
    ("Read", {"file_path": "api/webhooks.py"}, "Read 142 lines"),
    ("Grep", {"pattern": "hmac", "path": "api/"}, "3 matches in 2 files"),
    ("Edit", {"file_path": "api/webhooks.py"}, "Updated api/webhooks.py with 14 additions"),
    ("Bash", {"command": "python3 -m pytest api/tests -q"}, "31 passed in 3.4s"),
    ("Bash", {"command": "git diff --stat"}, "2 files changed, 16 insertions(+)"),
]


def type_out(text: str, delay: float = 0.035) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_stop_hook(host: str = "claude") -> str | None:
    """Invoke the real bundled hook the way hooks/hooks.json does — once,
    at the end of the turn — and return its systemMessage, if any."""
    proc = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), "--hook", "--host", host],
        capture_output=True,
        text=True,
        timeout=15,
    )
    try:
        return json.loads(proc.stdout or "{}").get("systemMessage")
    except json.JSONDecodeError:
        return None


def print_hook_message(message: str) -> None:
    lines = message.splitlines() or [message]
    first, rest = lines[0], lines[1:]
    wrapped = textwrap.wrap(first, width=88) or [first]
    sys.stdout.write(f"  ⎿  {CYAN}Stop hook:{RESET} {wrapped[0]}\n")
    for cont in wrapped[1:]:
        sys.stdout.write(f"       {cont}\n")
    for line in rest:
        sys.stdout.write(f"       {line.strip()}\n")
    sys.stdout.flush()


def main() -> int:
    # Wipe the launch command off screen so the recording opens on a clean session.
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    time.sleep(0.8)
    sys.stdout.write(f"{DIM}>{RESET} ")
    sys.stdout.flush()
    type_out(PROMPT)
    time.sleep(1.0)

    for tool, tool_input, result in CALLS:
        arg = next(iter(tool_input.values()))
        sys.stdout.write(f"\n{BOLD}●{RESET} {tool}({arg})\n")
        sys.stdout.flush()
        time.sleep(0.55)
        sys.stdout.write(f"  ⎿  {DIM}{result}{RESET}\n")
        sys.stdout.flush()
        time.sleep(0.4)

    # The turn ends here — this is the one point where the real Stop hook fires.
    time.sleep(0.5)
    message = run_stop_hook("claude")
    if message:
        print_hook_message(message)
        time.sleep(0.6)

    sys.stdout.write(f"\n{DIM}────────────────────────────────────────{RESET}\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
