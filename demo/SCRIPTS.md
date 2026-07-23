# Recording the launch video

`polyglot-launch.tape` drives [VHS](https://github.com/charmbracelet/vhs) to
produce `assets/demo/polyglot-launch.mp4` and `.gif`. It captures three
beats: a scripted agent session ending in the real Stop hook output, a tour
of the interactive 74-pair terminal cabinet, and a closing CTA line.

## What's genuine vs. staged

The tool calls and their results (`Read`, `Grep`, `Edit`, `Bash`, …) are
scripted for pacing against a fictional `webhook-signature-check` task — no
such session actually ran. The hook output is not staged: `demo/lib/
claude_session.py` shells out to the real `scripts/ambient.py --hook
--host claude`, the exact command `hooks/hooks.json` registers for the
`Stop` event, and prints whatever `systemMessage` it returns. Polyglot's
hook fires once per completed turn (not once per tool call), so the script
calls it once, after the scripted tool calls finish — matching the real
contract instead of a `PostToolUse`-style loop.

## Recording

```bash
# from the repo root
vhs demo/polyglot-launch.tape
```

`demo/lib/record_env.sh` points `$HOME` at a scratch directory before the
tape runs, so recording never reads or writes real Polyglot state; it seeds
a config with `en-de` active, ambient mode enabled, and cadence 1 so the
Stop hook has something to say on the very first turn.

`POLYGLOT_HOOK_SEED` (read by `polyglot.ambient.main`) is set in the tape so
reruns pick the same phrase deterministically.

Re-recording will overwrite `assets/demo/polyglot-launch.mp4` and `.gif` and
the beat screenshots in `demo/frames/`. Requires the `vhs` CLI and Python 3
on `PATH`.
