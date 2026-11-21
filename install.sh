#!/usr/bin/env bash
# Install or update the skill library for every harness on this machine (global scope), and the
# kiln look. Layers: agent-kit (this repo), then the private kit in $MY_SETUP/kit-private.
# Re-run after `git pull` here: the skills CLI copies into ~/.agents/skills and links each harness to it.
# Usage: ./install.sh [--pull] [--no-skills] [--no-look]
#   --no-skills  only the kiln look (dotfiles module `look` without `skills`)
#   --no-look    only the skills
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
PRIVATE="${MY_SETUP:-$HOME/code/my-setup}/kit-private"
export DO_NOT_TRACK=1   # no telemetry from the skills CLI
# Pinned on purpose: the CLI runs on every install and daily update, outside the vendor gates.
# 1.8+ is needed for repo@commit pins. Bump it by hand after reading its changelog.
SKILLS_CLI="skills@1.8.1"
# shellcheck source=design/kiln.sh
. "$KIT/design/kiln.sh" && k_init
SKILLS=1; LOOK=1
for a in "$@"; do
  case "$a" in
    --pull) git -C "$KIT" pull --ff-only -q || k_warn "agent-kit not pulled" "see: git -C $KIT status" ;;
    --no-skills) SKILLS=0 ;;
    --no-look) LOOK=0 ;;
  esac
done

# Shared look (design/, kiln): `kiln` on the PATH, and ~/.config/kiln plus Ghostty's theme links
# pointing at the theme in use (kiln the first time; `kiln use <theme>` switches).
if [ "$LOOK" = 1 ]; then
  mkdir -p "$HOME/.local/bin" && ln -sfn "$KIT/design/kiln.py" "$HOME/.local/bin/kiln"
  if python3 "$KIT/design/kiln.py" use >/dev/null; then
    k_ok "kiln look linked" "$(basename "$(readlink "${XDG_CONFIG_HOME:-$HOME/.config}/kiln")") theme; kiln list switches"
    k_init   # the glow of the theme just linked
  else
    k_warn "kiln themes not linked" "run: kiln use"
  fi
fi
[ "$SKILLS" = 1 ] || exit 0

command -v npx >/dev/null || { k_err "skills need node" "brew install node"; exit 1; }

k_run "skills from agent-kit" npx -y "$SKILLS_CLI" add "$KIT" -g -y --skill '*'
# Packs too big to copy into this repo, pinned in vendor.toml [[direct]].
export ARCHIFY_UPDATE_CHECK_DISABLED=1   # updates come through vendor.toml, not the skill's own check
python3 "$KIT/scripts/vendor.py" --direct | while read -r src skill; do
  k_run "skill $skill" npx -y "$SKILLS_CLI" add "$src" -g -y --skill "$skill"
done
if [ -d "$PRIVATE/skills" ]; then
  k_run "private skills from my-setup" npx -y "$SKILLS_CLI" add "$PRIVATE" -g -y --skill '*'
fi
n=$(find "$HOME/.agents/skills" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')
k_ok "$n skills for every harness" "list them: npx $SKILLS_CLI list -g"
