#!/usr/bin/env python3
"""Install a built wheel into a clean venv and verify its public surface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path


def _venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: check_wheel_install.py PATH_TO_WHEEL", file=sys.stderr)
        return 2
    wheel = Path(args[0]).resolve()
    if not wheel.is_file():
        print(f"wheel not found: {wheel}", file=sys.stderr)
        return 2

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    for filename in (
        "ambient-companion-v1.schema.json",
        "ambient-companion-v1.example.json",
    ):
        if not any(name.endswith(f"/protocol/{filename}") for name in names):
            print(f"wheel is missing packaged protocol fixture: {filename}", file=sys.stderr)
            return 1

    with tempfile.TemporaryDirectory(prefix="polyglot-wheel-") as temp:
        root = Path(temp)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = _venv_python(environment)
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel)],
            check=True,
        )
        result = subprocess.run(
            [str(python), "-m", "polyglot", "pairs", "--json"],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(root / "home")},
        )
        pairs = json.loads(result.stdout)
        assert len(pairs) == 74
        assert sum(pair["entries"] for pair in pairs) == 19_281
        entries_by_id = {pair["id"]: pair["entries"] for pair in pairs}
        assert entries_by_id["pl-en"] == 264
        assert entries_by_id["uk-en"] == 265
        assert entries_by_id["sv-en"] == 261
        assert entries_by_id["el-en"] == 256
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
