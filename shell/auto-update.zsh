# Keep the skill library current without a person: once a day, in the background, pull agent-kit
# and reinstall the skills if anything changed. Updates reach main only through the gated weekly
# vendor-update PR. Log: ~/.cache/agent-kit/update.log. Off: export AGENT_KIT_AUTO_UPDATE=0.
() {
  local kit="${AGENT_KIT:-$HOME/code/agent-kit}" cache="$HOME/.cache/agent-kit"
  [[ "${AGENT_KIT_AUTO_UPDATE:-1}" == 1 && -d "$kit/.git" ]] || return 0
  mkdir -p "$cache"
  local stamp="$cache/last-check"
  [[ -f "$stamp" && -n "$(find "$stamp" -mtime -1 2>/dev/null)" ]] && return 0
  touch "$stamp"
  (
    before="$(git -C "$kit" rev-parse HEAD)"
    git -C "$kit" pull --ff-only -q 2>&1 || exit 0
    [[ "$(git -C "$kit" rev-parse HEAD)" == "$before" ]] && exit 0
    echo "$(date '+%F %T') $before -> $(git -C "$kit" rev-parse --short HEAD)"
    git -C "$kit" log --format='  %s' "$before..HEAD"
    "$kit/install.sh" >/dev/null 2>&1 && echo "  installed" || echo "  install.sh failed"
  ) >> "$cache/update.log" 2>&1 &!
}
