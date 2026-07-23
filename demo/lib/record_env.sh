# Sourced by the VHS tape (Hidden) to isolate recording state.
# Points HOME at a scratch dir so hook_state.json and Polyglot's config are
# throwaway — real user state is never read or written.
# Usage: source record_env.sh [pair-id]

export HOME="$(mktemp -d /tmp/vhs-home-XXXXXX)"

if [ -n "$1" ]; then
  mkdir -p "$HOME/Library/Application Support/polyglot"
  printf '{"active_pair_id": "%s", "ambient_enabled": true, "ambient_cadence": 1}\n' "$1" \
    > "$HOME/Library/Application Support/polyglot/config.json"
fi
