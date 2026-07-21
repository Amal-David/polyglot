#!/usr/bin/env python3
"""Install a built wheel into a clean venv and verify its public surface."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
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
        assert len(pairs) == 70
        assert sum(pair["entries"] for pair in pairs) == 18_235
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
