# Polyglot

**One useful phrase at a time, while you work.**

Polyglot is a standalone language-learning skill and terminal companion with
70 language pairs and 18,235 bundled entries. Ask for a phrase on demand, open
the interactive cabinet, or opt into an occasional phrase after an AI agent
finishes a turn.

![Polyglot ambient phrase](assets/screenshots/polyglot_ambient_hook.png)

## What it feels like

```text
$ polyglot sample --pair en-es

🌍 hola  [oh-LAH]
   — "hello" (English → Spanish)
   [1/264 unique phrases shown]
```

Polyglot remembers the active pair and recently shown entries, prioritizing
unseen material before repeats.

## Demo video

[Watch the 20-second Polyglot demo](site/public/polyglot-demo.mp4).

The landing-page source lives in [`site/`](site/), with the full agent support
matrix and host-native ambient behavior documented alongside the video.

## Install

### Codex desktop and Codex CLI

```bash
codex plugin marketplace add Amal-David/polyglot
codex plugin add polyglot@polyglot
```

Restart the ChatGPT desktop app, open **Plugins**, select the **Polyglot**
marketplace, and install **Polyglot**. Its on-demand skill then appears in the
desktop Skills surface.

### Claude Code

```bash
claude plugin marketplace add Amal-David/polyglot
claude plugin install polyglot@polyglot
```

Use `/polyglot:polyglot` explicitly, or ask Claude for language practice and let
the skill match naturally.

### Pi

```bash
pi install git:github.com/Amal-David/polyglot
```

Pi loads the canonical skill and the native extension. Use
`/skill:polyglot` for on-demand practice or `/polyglot` for configuration.

### Hermes Agent

```bash
hermes plugins install Amal-David/polyglot --enable
```

Hermes registers the skill as `polyglot:polyglot`, an optional output
companion, and `/polyglot` configuration command.

### Python CLI

```bash
git clone https://github.com/Amal-David/polyglot.git
cd polyglot
python3 -m pip install .
```

The distribution is named `ambient-polyglot`; the import package and command
are both `polyglot`. It requires Python 3.10+ and has no Python runtime
dependencies.

## On demand vs. ambient

On-demand use is available immediately after installing the skill. Ambient
mode is deliberately disabled until you request it:

```bash
polyglot ambient enable --pair en-es --cadence 5
polyglot ambient status
polyglot ambient disable
```

Inside Pi or Hermes:

```text
/polyglot enable en-es 5
/polyglot status
/polyglot sample
/polyglot disable
```

The Codex and Claude skills can configure the same state using the bundled
standard-library script, so a separate Python package install is not required
for their plugin installs.

Ambient presentation follows each host's supported extension surface:

| Host | On demand | Ambient presentation |
|---|---|---|
| Codex desktop / CLI | Open Agent Skill | `Stop` event banner in the UI or event stream |
| Claude Code | Plugin skill | `Stop` `systemMessage` banner |
| Pi | Skill and `/polyglot` command | Native UI notification after `agent_end` |
| Hermes | Namespaced plugin skill and `/polyglot` command | Phrase appended by `transform_llm_output` |

Codex and Claude banners are lifecycle events, not assistant-authored response
text. Hermes can safely append to final response text through its native output
transform. Every adapter catches its own failures so Polyglot cannot break an
agent turn.

## CLI

```bash
polyglot                         # interactive 70-pair cabinet
polyglot pairs                   # list pair ids
polyglot pairs --json
polyglot pair en-ja              # set active pair
polyglot sample                  # sample from active pair
polyglot sample --pair es-en
polyglot sample --pair en-ko --json
polyglot ambient enable --pair en-fr --cadence 10
```

The pair catalog contains:

- 52 English-to-language directions.
- 18 language-to-English directions.
- Script, vocabulary, phrase, and sentence categories.
- Pronunciation hints and contextual notes where available.

## Educational content, not authoritative translation

Polyglot is designed for lightweight exposure and practice. Its translations,
romanizations, stress hints, and usage notes are educational content. They are
not a substitute for a qualified human translator or native-speaker review.

Do not rely on the bundled collection for medical, legal, emergency,
immigration, financial, safety-critical, or similarly consequential
communication.

## Correct a phrase

Native speakers and language educators are especially welcome. Please open a
**Language correction** issue with:

- Pair id, such as `en-es`.
- Exact source and target currently shown.
- Proposed correction.
- Region, register, or script context.
- A short source or rationale when possible.

See [DATA.md](DATA.md) for provenance, limitations, and the correction review
policy. Corrections should improve the source dataset and its tests rather than
patching generated output at runtime.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q polyglot scripts tests
python3 -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python3 scripts/check_wheel_install.py dist/ambient_polyglot-*.whl
```

The repository also contains manifests for Codex, Claude Code, Pi, and Hermes.
Host-specific validation requires the corresponding host CLI; unit tests cover
the shared contracts and failure isolation.

## License

[MIT](LICENSE)
