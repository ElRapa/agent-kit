# design: kiln, themes for every tool

kiln gives the terminal, the prompt, herdr, opencode, Gemini CLI, web pages, `ap` and the agent-stack edge
widget one look. Switch the theme in one place, and those tools pick it up.
Gallery of all themes, dark and light: `kiln gallery` opens `dist/gallery.html`.

```bash
kiln list                          # themes; ● marks the one in use
kiln use nightsky                  # switch (Ghostty: cmd+shift+, ; widget: reload Hammerspoon)
kiln lightswitch                   # flip every tool between dark and light (lightswitch auto: follow macOS)
kiln use --mode dark               # same, as part of a switch: always dark (or light, or auto)
kiln gallery                       # open the page with every theme
kiln installed                     # Ghostty themes and iTerm2 profiles already on this Mac
kiln import Dracula --name dracula # an installed Ghostty theme by name, a theme file, .itermcolors, or `iterm`
kiln build                         # after editing base.json or a theme; --check in CI
```

`kiln` is `design/kiln.py` (stdlib Python); agent-kit's `install.sh` puts it on the PATH
(`~/.local/bin/kiln`) and runs `kiln use` once.

## Themes

| Theme | Look |
|---|---|
| `kiln` | warm near-black and cream ink; the accent fades from dusk blue through violet to rose |
| `nightsky` | deep night blue, starlight ink in alpha steps, one twilight glow, translucent surfaces, few colours (cyan folds into blue) |
| `tokyo-night` | the theme Ghostty and herdr used before (Night and Day) |
| `catppuccin` | Mocha and Latte |
| `gruvbox` | dark and light |

Each has a dark and a light palette, so it follows macOS. `kiln lightswitch` (or `kiln use --mode dark|light`)
pins every tool to one mode: it points both Ghostty `kiln-current` names at that palette and writes
`~/.config/kiln-mode`, which `ap` and the widget read; `--mode auto` follows macOS again. `variants/nowu.json` shows a project
variant: it `extends` nightsky and changes only the glow.

## How it is built

- `base.json`: what every theme shares: fonts, spacing, glyphs, which colour plays which role
  (`accent`, `info`, `ok`, `warn`, `err`, `link`), and how roles map to the 16 terminal colours.
- `themes/<name>.json`: `modes.dark` and `modes.light` (16 named colours: five ink steps from `ink`
  to `faint`, surfaces, seven hues, selection), `glow` (the fading accent, a few stops per mode), and
  optionally `sky` (a page background gradient), `translucent` (opacity and blur), `semantic` or
  `ansi` overrides. Colours may carry alpha (`#rrggbbaa`): pages keep it, terminals get it blended
  onto the background.
- The idea of ink in steps with one accent comes from ponytail.dev and spaceship's "instrument"
  style: hierarchy from five steps of ink, colour only for what matters.

`kiln build` writes `dist/<theme>/`:

| File | For | How it is used |
|---|---|---|
| `ghostty/dark`, `ghostty/light` | Ghostty | `kiln use` links `kiln-current(-light)` to the theme in use and `kiln-<theme>(-light)` for each; dotfiles sets `theme = dark:kiln-current,light:kiln-current-light` |
| `herdr.toml` | herdr | for reference: `kiln use` and `kiln lightswitch` write the same tables into the kiln block of herdr's config (herdr has no include); reload with prefix+shift+r |
| (none) | opencode | `kiln use` sets `~/.config/opencode/cli.json` to opencode's `system` theme, which draws with the terminal's kiln colours, and its mode to the kiln mode |
| `starship.toml` | starship | copy to `~/.config/starship.toml`, or take only `[palettes.kiln]` |
| `gemini.json`, `gemini-light.json` | Gemini CLI | `"ui": { "theme": "<full path to ~/.config/kiln/gemini.json>" }` (Gemini loads theme files only below your home folder) |
| `tokens.css`, `components.css` | pages, reports, nowu | link or inline; classes start with `k-`, `.k-fade` gives text the glow |
| `theme.lua` | Hammerspoon widget | read from `~/.config/kiln/theme.lua` |
| `theme.json` | `ap` and anything else | resolved colours, glow, 16 ANSI colours per mode |

`~/.config/kiln` is a link to `dist/<theme in use>`, so a pull updates what reads from there.

`ap` and the pure prompt colour by ANSI slot (the terminal theme decides). In a truecolor terminal,
`ap` also fades its highlights through the theme's glow.

Rules: roles, not raw colours, in tools; the glow once or twice per screen; no colour for decoration;
dark and light both work. Commit `dist/`: other repos read it without running Python.
