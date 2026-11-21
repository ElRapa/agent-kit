# kiln style guide: how tools in this setup look, read and behave

`design/README.md` says what kiln is and how the themes are built. This page says how to use them
when you build something: a CLI command, an install script, a page, a widget. It is for people and
agents alike; the global AGENTS.md points here.

Why here: agent-kit is public and installed on every machine of the setup, the tokens live next door,
and every repo already reads kiln from `~/.config/kiln`. A guide in one tool's repo would only reach
that tool.

Two things are kept apart on purpose (agent-stack `docs/research/cli-ux.md`):

- **UX**: how a tool guides you. The first run, what it tells you next, how it fails.
- **Look**: colour, type, glyphs, spacing.

A tool can look good and still leave you lost. Get the UX right first.

## Principles

1. **Ink in steps, one accent.** Hierarchy comes from five steps of ink (`ink`, `soft`, `muted`,
   `faint`) and weight. Colour only says something: accent, info, ok, warn, err, link.
2. **The glow is a highlight, not a texture.** Once or twice per screen: the tool's name, the one
   thing to look at. Never on whole paragraphs.
3. **Roles, never hex.** Terminals use the 16 ANSI slots by role; pages use the CSS variables; the
   widget uses `theme.lua`. The theme decides the real colour, so every theme works.
4. **Dark and light both work.** Check both (`kiln lightswitch`). Never rely on a colour alone: a
   glyph or a word carries the meaning too.
5. **Plain stays plain.** With `NO_COLOR`, `TERM=dumb` or a pipe, print the plain text you would
   print without kiln. Scripts that parse output keep working. `FORCE_COLOR=1` turns colour on.
6. **Say what happens next.** Every run ends with what changed and the next command, never with a
   wall of logs.

## Terminal output

### Glyphs

One set everywhere, with ASCII stand-ins when the locale can't show them.

| Glyph | ASCII | Role | Means |
|---|---|---|---|
| `●` | `*` | glow | the tool's mark in a title; the active item (profile, theme) |
| `★` | `*` | glow | a place to start (the starred `ap` commands) |
| `✓` | `ok` | ok | done |
| `!` | `!` | warn | skipped, needs you later, or a todo |
| `✗` | `x` | err | failed; the line says why and how to fix it |
| `›` | `>` | info | something is running, or the cursor in a picker |
| `→` | `->` | accent | a command to run next, in bold, with a faint note |
| `◉` `○` | `[x]` `[ ]` | glow, faint | chosen, not chosen (pickers) |
| `·` | `-` | faint | separator inside one line |
| `│` | `\|` | faint | output of a command we ran, indented under its step |
| `━` `─` | `#` `-` | ok, faint | meters: filled, empty |

No emoji. No boxes around every block; whitespace groups.

### Shape of a run

```
  ● setup  dotfiles · agent-stack · agent-kit · my-setup      title: mark and name in the glow, tagline faint

  › installing: shell  ·  apps  ·  look                       what this run will do

  APPS                                                         a section kicker: upper case, bold, faint
    │ Using ghostty                                           a long command's output, behind a rule
  ✓ skills from agent-kit                                      a quiet step: spinner while it runs, then ✓
  ✗ clone my-setup  exit 128                                   a failure: what, then the end of its log
    │ fatal: could not read from remote repository
    full log: /tmp/kiln-run.Xa81

  DONE · 1m 12s                                                the summary, one line per part
  ✓ shell        zsh, git, prompt, secret
  ! personal     my-setup not cloned; agent-stack uses its examples

  NEXT
  → exec zsh              open a new shell with all of it      at most six, the most useful first
```

Rules:

- Two spaces of indent for everything; four under a step.
- One title per run. Sub-scripts a run calls (agent-stack's or agent-kit's install) print steps,
  not titles, and leave the NEXT list to the caller (`AP_INSTALL_NEXT=0`).
- Quiet steps (`k_run`) run behind a spinner and show their log only when they fail. Steps that may
  ask for a password or take minutes (`brew bundle`) stream through `k_stream` instead, so prompts
  stay visible.
- Errors: what failed, why if known, and the fix as a command. `✗ Homebrew is missing  install it
  from https://brew.sh, then run this again`. Errors go to stderr.
- Counts and times are welcome (`23 skills`, `took 21s`, `abc123 → def456, 3 new`).
- No spinner for anything under a second; no progress bars we can't fill truthfully.

### Questions and pickers

- Ask only when the answer changes what happens, and only once: keep the answer (install keeps the
  modules in `~/.config/dotfiles/modules`) and offer a way to change it (`--pick`).
- Every question has a default; Enter takes it. Without a terminal, take the default and say so.
- Every interactive choice has a flag (`--modules a,b`, `--yes`), so it can be scripted.
- Pickers: `↑↓` or `j k` move, space toggles, `a` all, `n` none, Enter goes, `q` quits without
  changing anything. The key line sits under the list in faint. Rows that can't be chosen here stay
  visible in faint with a note (`macOS only`, `always`). Dependencies follow automatically, and the
  picker says so in one info line (`widget needs agent-stack, so agent-stack is on too`).
- Descriptions: one line, what you get, in plain words. Not how it works.

### Help and home screens

`ap` is the reference: `ap` alone is a home screen grouped by task with the starred commands first,
`-h` adds examples, a typo gets "did you mean". New commands get a row in `ui.GROUPS`.

## Pages and the widget

- Pages inline or link `~/.config/kiln/tokens.css` and `components.css`; classes start with `k-`
  (`.k-fade` for the glow). Headings in the mono font at weight 800, labels in small tracked
  capitals, body in the sans. agent-stack's `docs/features.html` is the reference page.
- The Hammerspoon widget reads `theme.lua`; keep logic in Python (`ap status --json`), only drawing
  in Lua.
- Same glyphs and roles as the terminal. Meters: green, amber from 70 %, red from 90 %.

## Words

- Plain words, one idea per sentence, short lines. Say what the person gets, not what the code does.
- Name commands exactly as typed, in bold or code. Paths with `~/`, never a user name.
- Status words stay short: `ok`, `todo`, `skip`, `later`, `done`.

## Implementations

Use these instead of writing escape codes by hand.

| Language | Where | What it gives |
|---|---|---|
| shell (bash 3.2+, zsh) | `design/kiln.sh` | `k_init`, `k_title`, `k_head`, `k_step`, `k_ok`, `k_warn`, `k_err`, `k_hint`, `k_dim`, `k_c`, `k_fade`, `k_ask`; bash: `k_run` (spinner), `k_stream`, `k_pick` (checklist) |
| Python, agent-stack | `src/agent_stack/ui.py` | `Style` (roles, glyphs, `fade`, `head`, `bar`), `GROUPS` home screen, `style_report` for ok/todo lines |
| Python, stdlib only | `design/kiln.py` `UI` | the same rules for `kiln` itself; copy it into a stdlib tool that can't import agent-stack |
| pages | `dist/<theme>/tokens.css`, `components.css` | CSS variables by role, `k-` components |
| Hammerspoon | `dist/<theme>/theme.lua` | colours per mode and the glow stops |

The glow reaches the shell through `theme.sh` (`KILN_GLOW_DARK`, `KILN_GLOW_LIGHT`) and Python
through `theme.json`, both in `~/.config/kiln`. It is used only in truecolor terminals
(`COLORTERM=truecolor`); elsewhere the accent slot stands in.

## Checklist for a new tool or command

- [ ] Plain output unchanged with `NO_COLOR=1` or in a pipe; a test checks it.
- [ ] Glyphs from the table; ASCII when the locale can't show them.
- [ ] Colour by role; the glow at most twice per screen.
- [ ] Failures say how to fix them; errors on stderr.
- [ ] The run ends with what changed and what to run next.
- [ ] Every question has a default and a flag.
- [ ] Looked at in a dark and a light theme.
