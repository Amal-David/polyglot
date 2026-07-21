---
name: polyglot
description: This skill should be used when someone wants an educational language-learning phrase, vocabulary practice, pronunciation hints, a Polyglot language-pair selection, or configuration of Polyglot's optional ambient phrase mode.
---

# Polyglot

Offer short, low-friction language practice from Polyglot's bundled 74
directions and 19,281 educational entries.

## Sample a phrase

1. Identify the requested language direction, such as English to Spanish
   (`en-es`) or Spanish to English (`es-en`).
2. Run `polyglot pairs` when the available pair id is unclear.
3. Run `polyglot sample --pair <pair-id> --json` and read the returned fields.
4. If the installed command is unavailable, locate this `SKILL.md`, move two
   directories up to the plugin root, and run:

   `python3 <plugin-root>/scripts/ambient.py --sample --pair <pair-id> --json`

5. Present the target phrase, source meaning, pronunciation hint, and note when
   present. Keep practice concise unless a drill, quiz, or explanation was
   requested.

## Configure the active pair

- Run `polyglot pair <pair-id>` to change the pair used by future samples.
- Run `polyglot pair` to inspect the current pair.
- Do not enable ambient mode unless the user explicitly requests it.
- Run `polyglot ambient enable --pair <pair-id> --cadence <turns>` after that
  explicit request.
- Run `polyglot ambient disable` to stop automatic phrases.
- Run `polyglot ambient status` to report whether the active pair is ready for
  one ungraded starter exposure, waiting for explicit review, or has a due
  reviewed card.
- If the installed command is unavailable, use the bundled script instead:
  `python3 <plugin-root>/scripts/ambient.py --enable --pair <pair-id> --cadence <turns>`,
  `--disable`, or `--status`.

A fresh pair may receive one labelled starter exposure at the configured
cadence. It is not a recall grade and must not be described as progress. After
that first exposure, direct the user to `polyglot review`; once review state
exists, ambient delivery is due-only and never changes the schedule.

## Content boundaries

- Describe the collection as educational material, not an authoritative
  translation service.
- Treat pronunciation fields as approachable hints rather than phonetic
  guarantees.
- Avoid relying on bundled phrases for medical, legal, emergency, immigration,
  financial, or other high-stakes communication. Recommend a qualified human
  translator for those uses.
- Preserve the phrase exactly when reporting a suspected content error. Direct
  corrections to the repository process documented in `DATA.md`.
