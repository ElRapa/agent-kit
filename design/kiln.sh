# shellcheck shell=bash
# kiln.sh: the kiln look for shell scripts. Source it, then call k_init once.
#
#   . ~/code/agent-kit/design/kiln.sh && k_init
#   k_title setup "install"          a faded name and a tagline, once per run
#   k_head "apps"                    a section kicker: upper case, faint, bold
#   k_step "cloning agent-kit"       › something is happening
#   k_ok "linked 6 files"            ✓ done            k_warn "…"  ! skipped    k_err "…"  ✗ failed (stderr)
#   k_hint "exec zsh" "open a new shell"     → a command to run next, with what it does
#   k_c faint "text"                 one role around text: bold dim accent info ok warn err faint
#   k_fade "text"                    text in the theme's glow (truecolor), else bold accent
#   k_ask "Install now?" y           yes/no from the terminal; the second word is the default
#   k_run "label" cmd …              (bash) a spinner while cmd runs quietly; its log on failure
#   k_stream cmd …                   (bash) cmd's output, indented behind a faint rule
#   k_pick                           (bash) a checklist picker, see the function
#
# How it should look and read: design/STYLE.md. Colour by ANSI role, so the terminal's kiln theme
# decides the real colour; the glow comes from ~/.config/kiln/theme.sh (kiln build writes it).
# Colour is off with NO_COLOR, TERM=dumb or when stdout is not a terminal; FORCE_COLOR turns it on.
# Glyphs fall back to ASCII when the locale is not UTF-8. Printing works in bash 3.2 and zsh.

k_init() {
  K_COLOR=0
  K_UNI=1
  K_GLOW=""
  if [ -n "${NO_COLOR:-}" ]; then K_COLOR=0
  elif [ -n "${FORCE_COLOR:-}${CLICOLOR_FORCE:-}" ]; then K_COLOR=1
  elif [ "${TERM:-dumb}" != dumb ] && [ -t 1 ]; then K_COLOR=1
  fi
  case "${LC_ALL:-${LC_CTYPE:-${LANG:-}}}" in
    *UTF-8* | *utf-8* | *UTF8* | *utf8*) K_UNI=1 ;;
    "") [ "$(uname)" = Darwin ] && K_UNI=1 || K_UNI=0 ;;
    *) K_UNI=0 ;;
  esac
  K_MODE="${KILN_MODE:-}"
  if [ -z "$K_MODE" ] && [ -r "${XDG_CONFIG_HOME:-$HOME/.config}/kiln-mode" ]; then
    K_MODE="$(cat "${XDG_CONFIG_HOME:-$HOME/.config}/kiln-mode" 2>/dev/null)"
  fi
  case "$K_MODE" in
    dark | light) ;;
    *) if [ "$(uname)" = Darwin ] && ! defaults read -g AppleInterfaceStyle >/dev/null 2>&1; then
         K_MODE=light
       else K_MODE=dark; fi ;;
  esac
  local theme="${XDG_CONFIG_HOME:-$HOME/.config}/kiln/theme.sh"
  case "${COLORTERM:-}" in
    truecolor | 24bit)
      if [ "$K_COLOR" = 1 ] && [ -r "$theme" ]; then
        # shellcheck disable=SC1090
        . "$theme"
        if [ "$K_MODE" = light ]; then K_GLOW="${KILN_GLOW_LIGHT:-}"; else K_GLOW="${KILN_GLOW_DARK:-}"; fi
      fi ;;
  esac
  # the stops as numbers, once: k_r0 k_g0 k_b0, k_r1 …; K_NSTOPS of them
  K_NSTOPS=0
  local x
  # shellcheck disable=SC2116 # echo: zsh splits command output, not variables
  for x in $(echo "$K_GLOW"); do
    eval "k_r$K_NSTOPS=\$((16#${x:1:2})) k_g$K_NSTOPS=\$((16#${x:3:2})) k_b$K_NSTOPS=\$((16#${x:5:2}))"
    K_NSTOPS=$((K_NSTOPS + 1))
  done
}

# The escape for one role (empty when colour is off).
k_sgr() {
  [ "${K_COLOR:-0}" = 1 ] || return 0
  local codes="" r
  for r in $(echo "$1" | tr ',' ' '); do
    case "$r" in
      bold) r=1 ;; dim) r=2 ;; italic) r=3 ;; accent) r=35 ;; info) r=36 ;; ok) r=32 ;;
      warn) r=33 ;; err) r=31 ;; faint) r=90 ;; ink) r=39 ;; *) continue ;;
    esac
    codes="${codes:+$codes;}$r"
  done
  [ -n "$codes" ] && printf '\033[%sm' "$codes"
  return 0
}

# k_c ROLE[,ROLE] TEXT: text in a role, e.g. k_c bold,accent "name".
k_c() {
  if [ "${K_COLOR:-0}" = 1 ] && [ -n "$2" ]; then printf '%s%s\033[0m' "$(k_sgr "$1")" "$2"
  else printf '%s' "$2"; fi
}

# A glyph, or its ASCII stand-in.
k_g() {
  local u a
  case "$1" in
    dot) u="●" a="*" ;; ok) u="✓" a="ok" ;; warn) u="!" a="!" ;; err) u="✗" a="x" ;;
    star) u="★" a="*" ;; arrow) u="→" a="->" ;; prompt) u="›" a=">" ;; sep) u="·" a="-" ;;
    on) u="◉" a="[x]" ;; off) u="○" a="[ ]" ;; rule) u="│" a="|" ;; ask) u="?" a="?" ;;
    full) u="━" a="#" ;; empty) u="─" a="-" ;; *) u="$1" a="$1" ;;
  esac
  if [ "${K_UNI:-1}" = 1 ]; then printf '%s' "$u"; else printf '%s' "$a"; fi
}

# k_fade TEXT [START END]: text across the glow from START to END percent (default 0 100).
k_fade() {
  local t="$1" s="${2:-0}" e="${3:-100}"
  if [ "${K_COLOR:-0}" != 1 ] || [ -z "$t" ]; then printf '%s' "$t"; return 0; fi
  if [ "${K_NSTOPS:-0}" = 0 ]; then printf '\033[1;35m%s\033[0m' "$t"; return 0; fi
  local m=$K_NSTOPS n=${#t} i=0 out="" pos seg f j k r g b ra ga ba rb gb bb
  if [ "$m" = 1 ]; then eval "r=\$k_r0 g=\$k_g0 b=\$k_b0"; s=0; e=0; fi
  while [ "$i" -lt "$n" ]; do
    if [ "$m" -gt 1 ]; then
      if [ "$n" -gt 1 ]; then pos=$((s * 1000 + (e - s) * 1000 * i / (n - 1))); else pos=$((s * 1000)); fi
      seg=$((pos * (m - 1) / 100)) # 0 .. (m-1)*1000
      j=$((seg / 1000))
      [ "$j" -ge $((m - 1)) ] && j=$((m - 2))
      f=$((seg - j * 1000))
      k=$((j + 1))
      eval "ra=\$k_r$j ga=\$k_g$j ba=\$k_b$j rb=\$k_r$k gb=\$k_g$k bb=\$k_b$k"
      r=$((ra + (rb - ra) * f / 1000)) g=$((ga + (gb - ga) * f / 1000)) b=$((ba + (bb - ba) * f / 1000))
    fi
    out="$out"$'\033'"[38;2;${r};${g};${b}m${t:$i:1}"
    i=$((i + 1))
  done
  printf '\033[1m%s\033[0m' "$out"
}

k_title() { printf '\n  %s %s  %s\n\n' "$(k_fade "$(k_g dot)" 0 0)" "$(k_fade "$1")" "$(k_c faint "${2:-}")"; }
k_head() { printf '\n  %s\n' "$(k_c bold,faint "$(echo "$1" | tr '[:lower:]' '[:upper:]')")"; }
k_step() { printf '  %s %s\n' "$(k_c info "$(k_g prompt)")" "$1"; }
k_ok() { printf '  %s %s%s\n' "$(k_c ok "$(k_g ok)")" "$1" "${2:+  $(k_c faint "$2")}"; }
k_warn() { printf '  %s %s%s\n' "$(k_c warn "$(k_g warn)")" "$1" "${2:+  $(k_c faint "$2")}"; }
k_err() { printf '  %s %s%s\n' "$(k_c err "$(k_g err)")" "$1" "${2:+  $(k_c faint "$2")}" >&2; }
k_dim() { printf '    %s\n' "$(k_c faint "$1")"; }
k_hint() { printf '  %s %s%s\n' "$(k_c accent "$(k_g arrow)")" "$(k_c bold "$1")" "${2:+  $(k_c faint "$2")}"; }

# k_ask QUESTION [y|n]: 0 for yes. Reads the terminal; without one it takes the default.
k_ask() {
  local def="${2:-y}" a hint="[Y/n]"
  [ "$def" = n ] && hint="[y/N]"
  if ! { [ -t 0 ] || [ -r /dev/tty ]; } 2>/dev/null; then [ "$def" = y ]; return; fi
  printf '  %s %s %s ' "$(k_c accent "$(k_g ask)")" "$1" "$(k_c faint "$hint")"
  IFS= read -r a </dev/tty || a=""
  case "${a:-$def}" in y* | Y* | j* | J*) return 0 ;; *) return 1 ;; esac
}

# --- bash only below (arrays, PIPESTATUS) ----------------------------------------------------

# k_run LABEL CMD…: run CMD quietly behind a spinner; ✓ LABEL, or ✗ with the end of its log.
# For steps that never ask anything (stdin is /dev/null). Long or chatty steps: k_stream.
k_run() {
  local label="$1" log rc=0 i=0 frames="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
  shift
  log="$(mktemp "${TMPDIR:-/tmp}/kiln-run.XXXXXX")"
  if [ "${K_COLOR:-0}" = 1 ] && [ "${K_UNI:-1}" = 1 ]; then
    "$@" </dev/null >"$log" 2>&1 &
    local pid=$!
    printf '\033[?25l'
    while kill -0 "$pid" 2>/dev/null; do
      printf '\r  %s %s' "$(k_fade "${frames:$((i % 10)):1}" $((i * 7 % 100)) $((i * 7 % 100)))" "$(k_c faint "$label")"
      i=$((i + 1))
      sleep 0.08
    done
    wait "$pid" || rc=$?
    printf '\r\033[2K\033[?25h'
  else
    "$@" </dev/null >"$log" 2>&1 || rc=$?
  fi
  if [ "$rc" = 0 ]; then
    k_ok "$label"
    rm -f "$log"
  else
    k_err "$label" "exit $rc"
    tail -n 12 "$log" | while IFS= read -r line; do printf '    %s %s\n' "$(k_c faint "$(k_g rule)")" "$line" >&2; done
    k_dim "full log: $log" >&2
  fi
  return "$rc"
}

# k_stream CMD…: CMD's output, each line behind a faint rule, so it reads as part of a step.
k_stream() {
  local bar
  bar="$(k_c faint "$(k_g rule)")"
  "$@" 2>&1 | while IFS= read -r line; do printf '    %s %s\n' "$bar" "$line"; done
  return "${PIPESTATUS[0]}"
}

# k_pick: a checklist in the terminal. ↑/↓ or j/k move, space toggles, a all, n none, enter takes it,
# q quits (returns 1). Set before calling:
#   K_ITEMS=(name …)  K_DESC=(one line each …)  K_STATE=(1 on | 0 off | L always on | X unavailable …)
#   K_NOTE=(short right-hand note or "" …)      K_PICK_TITLE="pick modules"
# Optional: define k_pick_hook INDEX, called after a toggle, to keep dependencies right; it may set
# K_MSG to a line shown under the list. Reads keys from /dev/tty, draws on stdout.
k_pick() {
  local n=${#K_ITEMS[@]} cur=0 key rest i lines cols w drawn=0
  K_MSG=""
  while [ "$cur" -lt "$n" ] && { [ "${K_STATE[$cur]}" = X ] || [ "${K_STATE[$cur]}" = L ]; }; do cur=$((cur + 1)); done
  [ "$cur" -lt "$n" ] || cur=0
  cols=$(tput cols 2>/dev/null || echo 80)
  w=0
  for i in "${K_ITEMS[@]}"; do [ ${#i} -gt "$w" ] && w=${#i}; done
  lines=$((n + 3))
  printf '\033[?25l'
  k_head "${K_PICK_TITLE:-pick}"
  while :; do
    [ "$drawn" = 1 ] && printf '\033[%dA' "$lines"
    drawn=1
    for ((i = 0; i < n; i++)); do
      local st="${K_STATE[$i]}" mark box name desc note max
      if [ "$i" = "$cur" ]; then mark="$(k_c accent "$(k_g prompt)")"; else mark=" "; fi
      case "$st" in
        1) box="$(k_fade "$(k_g on)" $((i * 100 / (n > 1 ? n - 1 : 1))) $((i * 100 / (n > 1 ? n - 1 : 1))))" ;;
        L) box="$(k_c faint "$(k_g on)")" ;;
        *) box="$(k_c faint "$(k_g off)")" ;;
      esac
      name="$(printf "%-${w}s" "${K_ITEMS[$i]}")"
      case "$st" in
        1 | L) name="$(k_c bold "$name")" ;;
        X) name="$(k_c faint "$name")" ;;
      esac
      note="${K_NOTE[$i]:-}"
      max=$((cols - w - ${#note} - 12))
      [ "$max" -lt 10 ] && max=10
      desc="${K_DESC[$i]}"
      [ ${#desc} -gt "$max" ] && desc="${desc:0:$((max - 1))}…"
      [ "$i" = "$cur" ] && [ "$st" != X ] || desc="$(k_c faint "$desc")"
      printf '\033[2K  %s %s %s  %s%s\n' "$mark" "$box" "$name" "$desc" "${note:+  $(k_c faint,italic "$note")}"
    done
    printf '\033[2K\n'
    printf '\033[2K  %s\n' "$(k_c faint "↑↓ move  $(k_g sep)  space toggle  $(k_g sep)  a all  $(k_g sep)  n none  $(k_g sep)  enter go  $(k_g sep)  q quit")"
    printf '\033[2K  %s\n' "$(k_c info "$K_MSG")"
    IFS= read -rsn1 key </dev/tty || { printf '\033[?25h'; return 1; }
    if [ "$key" = $'\033' ]; then IFS= read -rsn2 -t 1 rest </dev/tty || rest=""; key="$key$rest"; fi
    K_MSG=""
    case "$key" in
      $'\033[A' | k) i=$cur; while :; do i=$(((i - 1 + n) % n)); [ "${K_STATE[$i]}" != X ] && break; [ "$i" = "$cur" ] && break; done; cur=$i ;;
      $'\033[B' | j) i=$cur; while :; do i=$(((i + 1) % n)); [ "${K_STATE[$i]}" != X ] && break; [ "$i" = "$cur" ] && break; done; cur=$i ;;
      " " | x)
        case "${K_STATE[$cur]}" in
          1) K_STATE[$cur]=0 ;; 0) K_STATE[$cur]=1 ;;
          L) K_MSG="${K_ITEMS[$cur]} is always installed" ;;
        esac
        declare -F k_pick_hook >/dev/null && k_pick_hook "$cur" ;;
      a) for ((i = 0; i < n; i++)); do [ "${K_STATE[$i]}" = 0 ] && K_STATE[$i]=1; done
         declare -F k_pick_hook >/dev/null && k_pick_hook -1 ;;
      n) for ((i = 0; i < n; i++)); do [ "${K_STATE[$i]}" = 1 ] && K_STATE[$i]=0; done
         declare -F k_pick_hook >/dev/null && k_pick_hook -1 ;;
      "") break ;;
      q | $'\033') printf '\033[?25h'; return 1 ;;
    esac
  done
  printf '\033[?25h'
  return 0
}
