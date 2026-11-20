# design: kiln, one look for every tool

One tokens file, `tokens.json`, sets the colours, type and glyphs for the terminal, the prompt, web
pages and the agent-stack edge widget. `build.py` (stdlib Python) turns it into each tool's format.
Preview: open `dist/kiln/preview.html`.

The look: warm near-black surfaces, cream ink in five steps, JetBrains Mono at weight 800 for
headings and labels with an italic muted second line, small tracked capitals for labels, and colour
only where it means something (violet accent, cyan info, green/amber/red state). A cyan-violet-pink
glow is for one thing per screen. Inspired by the terminal style of ponytail.dev; the values and
components are our own.

## Files

| Built file (`dist/kiln/`) | For | How it gets there |
|---|---|---|
| `ghostty/kiln`, `ghostty/kiln-light` | Ghostty | `install.sh` links them into `~/.config/ghostty/themes`; dotfiles sets `theme = dark:kiln,light:kiln-light` |
| `herdr.toml` | herdr | paste its `[theme.custom]` into dotfiles' herdr config (herdr has no include) |
| `starship.toml` | starship | copy to `~/.config/starship.toml`, or take only `[palettes.kiln]` |
| `gemini.json` | Gemini CLI | `"ui": { "theme": "<full path to ~/.config/kiln/gemini.json>" }` in `~/.gemini/settings.json` (Gemini loads theme files only below your home folder) |
| `tokens.css`, `components.css` | web pages, reports, nowu | link or inline them; classes start with `k-` |
| `kiln.lua` | Hammerspoon (agent-stack widget) | read from `~/.config/kiln/kiln.lua` |
| `kiln.json` | anything else | every colour resolved, plus the 16 ANSI colours per mode |

`install.sh` links `~/.config/kiln` to `dist/kiln`, so a pull updates everything that reads from
there.

The CLI (`ap`) and the pure prompt use the 16 ANSI colours by role (magenta is the accent, cyan info,
green/yellow/red state), so they follow whatever the terminal theme is. With kiln in Ghostty, they
are kiln.

## Change it

```bash
python3 design/build.py                       # after editing tokens.json
python3 design/build.py variants/nowu.json    # a variant: tokens.json plus the keys that differ
python3 design/build.py --check               # CI: fails when dist/ is not rebuilt
```

A project with its own accent adds `variants/<name>.json` with only what differs, e.g.
`{"name": "nowu", "semantic": {"accent": "cyan"}}`, and gets `dist/<name>/` with every file. Commit
`dist/`: other repos read it without running Python.

Rules: roles, not raw colours, in tools (`accent`, `ok`, `warn`, …); one glow per screen; no colour
for decoration; dark and light both work.
