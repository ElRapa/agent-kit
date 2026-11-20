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

# Shared look (design/, kiln): `kiln` on the PATH, and ~/.config/kiln plus Ghostty's theme links
# pointing at the theme in use (kiln the first time; `kiln use <theme>` switches).
mkdir -p "$HOME/.local/bin" && ln -sfn "$KIT/design/kiln.py" "$HOME/.local/bin/kiln"
python3 "$KIT/design/kiln.py" use >/dev/null || echo "skip: kiln themes not linked" >&2

command -v npx >/dev/null || { echo "needs node (brew install node)" >&2; exit 1; }

npx -y "$SKILLS_CLI" add "$KIT" -g -y --skill '*'
# Packs too big to copy into this repo, pinned in vendor.toml [[direct]].
export ARCHIFY_UPDATE_CHECK_DISABLED=1   # updates come through vendor.toml, not the skill's own check
python3 "$KIT/scripts/vendor.py" --direct | while read -r src skill; do
  npx -y "$SKILLS_CLI" add "$src" -g -y --skill "$skill"
done
[ -d "$PRIVATE/skills" ] && npx -y "$SKILLS_CLI" add "$PRIVATE" -g -y --skill '*'
npx -y "$SKILLS_CLI" list -g
