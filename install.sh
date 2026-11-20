#!/usr/bin/env bash
# Install or update the skill library for every harness on this machine (global scope).
# Layers: agent-kit (this repo), then the private kit in $MY_SETUP/kit-private when it exists.
# Re-run after `git pull` here: the skills CLI copies into ~/.agents/skills and links each harness to it.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
PRIVATE="${MY_SETUP:-$HOME/code/my-setup}/kit-private"
export DO_NOT_TRACK=1   # no telemetry from the skills CLI
# Pinned on purpose: the CLI runs on every install and daily update, outside the vendor gates.
# 1.8+ is needed for repo@commit pins. Bump it by hand after reading its changelog.
SKILLS_CLI="skills@1.8.1"

[ "${1:-}" = "--pull" ] && git -C "$KIT" pull --ff-only

# Shared look (design/, kiln): link the built themes where tools look for them. Links, so a pull
# updates them; a real file of yours at those paths is left alone.
link() { [ -e "$2" ] && [ ! -L "$2" ] && { echo "skip $2: not a link" >&2; return; }; mkdir -p "$(dirname "$2")"; ln -sfn "$1" "$2"; }
link "$KIT/design/dist/kiln" "${XDG_CONFIG_HOME:-$HOME/.config}/kiln"
link "$KIT/design/dist/kiln/ghostty/kiln" "${XDG_CONFIG_HOME:-$HOME/.config}/ghostty/themes/kiln"
link "$KIT/design/dist/kiln/ghostty/kiln-light" "${XDG_CONFIG_HOME:-$HOME/.config}/ghostty/themes/kiln-light"

command -v npx >/dev/null || { echo "needs node (brew install node)" >&2; exit 1; }

npx -y "$SKILLS_CLI" add "$KIT" -g -y --skill '*'
# Packs too big to copy into this repo, pinned in vendor.toml [[direct]].
export ARCHIFY_UPDATE_CHECK_DISABLED=1   # updates come through vendor.toml, not the skill's own check
python3 "$KIT/scripts/vendor.py" --direct | while read -r src skill; do
  npx -y "$SKILLS_CLI" add "$src" -g -y --skill "$skill"
done
[ -d "$PRIVATE/skills" ] && npx -y "$SKILLS_CLI" add "$PRIVATE" -g -y --skill '*'
npx -y "$SKILLS_CLI" list -g
