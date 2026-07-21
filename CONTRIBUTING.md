# Contributing

Thanks for improving Polyglot. Language corrections, accessibility
improvements, host-adapter fixes, and focused documentation changes are
welcome.

## Set up

Polyglot requires Python 3.10+ and has no Python runtime dependencies.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

On Windows, activate with `.venv\Scripts\activate`.

## Language corrections

Read [DATA.md](DATA.md) first. Include the exact current entry, proposed
correction, regional or register context, and a source or native-speaker
rationale. Keep reverse-direction pairs in mind, but do not make mechanical
reverse translations when natural wording differs.

## Code changes

- Keep the Python runtime standard-library-only.
- Preserve the `polyglot` app-data directory and existing active-pair/history
  fields.
- Keep ambient mode opt-in.
- Catch adapter failures so a phrase can never break an agent turn.
- Keep one canonical Agent Skill at `skills/polyglot/SKILL.md`.
- Avoid duplicating phrase-selection logic inside host adapters.
- Do not edit an agent's global settings file as an installation shortcut.

Run before submitting:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q polyglot scripts tests
python3 -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python3 scripts/check_wheel_install.py dist/ambient_polyglot-*.whl
git diff --check
```

When changing a native adapter, also load it with the corresponding host CLI
when available and state which host/version was actually tested.

## Pull requests

Keep changes focused and explain the user-visible behavior. Do not claim
translation, plugin, or host compatibility that was not tested. By submitting a
contribution, you agree to license it under the repository's MIT license.
