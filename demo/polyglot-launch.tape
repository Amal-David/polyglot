# Polyglot launch video — run from the repo root: vhs demo/polyglot-launch.tape
# Beat 1: agent session with the real Stop hook firing (en-de pair, genuine hook output)
# Beat 2: the polyglot TUI (74 language pairs)
# Beat 3: CTA

Require python3

# Separate path (assets/demo/vhs/) so this never collides with the existing
# hand-recorded hero at assets/demo/polyglot-claude-demo.gif — see the PR
# description for how to swap or combine them in the README.
Output assets/demo/vhs/polyglot-launch.mp4
Output assets/demo/vhs/polyglot-launch.gif

Set Theme "Catppuccin Mocha"
Set FontSize 20
Set Width 1560
Set Height 760
Set Padding 12
Set TypingSpeed 40ms
Set Framerate 30
Set WindowBar Colorful
Set WindowBarSize 36

Env POLYGLOT_HOOK_SEED "2"

# --- setup (hidden): scratch HOME with en-de as the active, ambient-enabled pair ---
Hide
Type "source demo/lib/record_env.sh en-de && clear"
Enter
Type "python3 demo/lib/claude_session.py"
Enter
Sleep 500ms
Show

# --- beat 1: session + hero phrase ---
Wait+Screen@30s /Stop hook:/
Screenshot demo/frames/polyglot-hero.png
Sleep 4.5s
Wait@15s
Sleep 1s

# --- beat 2: the TUI ---
Hide
Type "clear"
Enter
Show
Type "python3 -m polyglot"
Enter
Sleep 2.5s
Screenshot demo/frames/polyglot-grid.png
Down@250ms 3
Sleep 800ms
Right@250ms 2
Sleep 800ms
Enter
Sleep 2s
Screenshot demo/frames/polyglot-detail.png
Down@300ms 4
Sleep 1.5s
Type "q"
Sleep 800ms
Type "q"
Sleep 1.5s

# --- beat 3: CTA ---
Hide
Enter
Sleep 300ms
Type "clear"
Enter
Sleep 300ms
Show
Type@60ms "# 74 language pairs · 19,281 phrases · one hook — github.com/Amal-David/polyglot"
Sleep 4s
Screenshot demo/frames/polyglot-cta.png
