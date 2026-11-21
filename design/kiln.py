#!/usr/bin/env python3
"""kiln: themes for every tool in this setup, from one base and one file per theme (stdlib only).

    kiln list                         themes, and which one is in use
    kiln use nightsky                 switch: Ghostty, the widget, ap and pages follow
    kiln import FILE [--light FILE] --name NAME    a Ghostty or iTerm2 theme -> themes/NAME.json
    kiln build                        rebuild dist/ after editing base.json or a theme
    kiln build --check                CI: exit 1 when dist/ is stale

base.json holds what every theme shares (type, glyphs, roles, how roles map to the 16 terminal
colours). themes/<name>.json holds a palette for dark and light, the glow (a fading accent) and
anything that differs. variants/<name>.json is a theme that `extends` another and changes a few keys.
Colours may carry alpha (#rrggbbaa): pages keep it, terminals get it blended onto the background.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import sys
from pathlib import Path
from typing import Any, ClassVar

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
MODES = ("dark", "light")
ANSI = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
NAMES = ["bg", "surface", "raised", "line", "ink", "soft", "muted", "faint",
         "cyan", "violet", "pink", "amber", "green", "red", "blue", "selection"]
HERDR = {  # herdr theme.custom token -> colour name
    "accent": "accent", "panel_bg": "bg", "sidebar_bg": "surface", "active_row_bg": "raised",
    "selection_bg": "selection", "surface0": "surface", "surface1": "raised", "surface_dim": "bg",
    "overlay0": "faint", "overlay1": "muted", "text": "ink", "subtext0": "muted", "mauve": "violet",
    "green": "green", "yellow": "amber", "red": "red", "blue": "blue", "teal": "cyan", "peach": "pink",
}


# --- terminal output in the kiln look (design/STYLE.md) ------------------------------------------

class UI:
    """kiln's own output: ANSI roles, ● ✓ ! ✗ → glyphs, the glow of the theme in use in truecolor.

    Off with NO_COLOR, TERM=dumb or a pipe (FORCE_COLOR turns it on); ASCII glyphs when the stream
    cannot encode them. Same rules as `ap` (agent-stack ui.Style) and design/kiln.sh."""

    CODES: ClassVar[dict[str, str]] = {"bold": "1", "faint": "90", "accent": "35", "info": "36", "ok": "32", "warn": "33", "err": "31"}
    GLYPHS: ClassVar[dict[str, tuple[str, str]]] = {"dot": ("●", "*"), "ok": ("✓", "ok"), "warn": ("!", "!"), "err": ("✗", "x"), "arrow": ("→", "->"),
              "sep": ("·", "-")}

    def __init__(self, stream: Any = None) -> None:
        self.stream = stream or sys.stdout
        if os.environ.get("NO_COLOR"):
            self.color = False
        elif os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE"):
            self.color = True
        else:
            self.color = os.environ.get("TERM") != "dumb" and hasattr(self.stream, "isatty") and self.stream.isatty()
        try:
            "●✓✗→·".encode(getattr(self.stream, "encoding", None) or "ascii")
            self.unicode = True
        except (UnicodeEncodeError, LookupError):
            self.unicode = False
        self.glow: list[tuple[int, int, int]] = []

    def use_glow(self, stops: list[str]) -> None:
        if self.color and os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
            self.glow = [rgba(x)[:3] for x in stops]

    def c(self, text: str, *roles: str) -> str:
        if not self.color or not text or not roles:
            return text
        return f"\033[{';'.join(self.CODES[r] for r in roles)}m{text}\033[0m"

    def g(self, name: str) -> str:
        u, a = self.GLYPHS[name]
        return u if self.unicode else a

    def fade(self, text: str, start: float = 0.0, end: float = 1.0) -> str:
        if not self.color or not text:
            return text
        if len(self.glow) < 2:
            return self.c(text, "bold", "accent")
        out = []
        for i, ch in enumerate(text):
            t = (start + (end - start) * i / max(1, len(text) - 1)) * (len(self.glow) - 1)
            j = min(int(t), len(self.glow) - 2)
            a, b = self.glow[j], self.glow[j + 1]
            r, g, bl = (round(x + (y - x) * (t - j)) for x, y in zip(a, b, strict=True))
            out.append(f"\033[38;2;{r};{g};{bl}m{ch}")
        return "\033[1m" + "".join(out) + "\033[0m"

    def title(self, name: str, tagline: str = "") -> None:
        print(f"\n  {self.fade(self.g('dot'), 0, 0)} {self.fade(name)}  {self.c(tagline, 'faint')}\n", file=self.stream)

    def line(self, role: str, what: str, detail: str = "", tool: str = "", width: int = 9) -> None:
        glyph = {"ok": "ok", "warn": "warn", "err": "err", "info": "arrow"}[role]
        head = self.c(f"{tool:<{width}}", "bold") + " " if tool else ""
        tail = "  " + self.c(detail, "faint") if detail else ""
        print(f"  {self.c(self.g(glyph), 'accent' if role == 'info' else role)} {head}{what}{tail}", file=self.stream)


def _ui(stream: Any = None) -> UI:
    ui = UI(stream)
    cur = CONFIG / "kiln" / "theme.json"
    try:
        data = json.loads(cur.read_text())
        mode = current_mode()
        if mode == "auto":
            mode = macos_mode()
        ui.use_glow(data["glow"][mode])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return ui


# --- colour helpers -----------------------------------------------------------------------------

def rgba(h: str) -> tuple[int, int, int, float]:
    h = h.lstrip("#")
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a


def hexc(r: float, g: float, b: float) -> str:
    return "#" + "".join(f"{max(0, min(255, round(x))):02x}" for x in (r, g, b))


def mix(a: str, b: str, t: float) -> str:
    ra, rb = rgba(a), rgba(b)
    return hexc(*(x + (y - x) * t for x, y in zip(ra[:3], rb[:3], strict=True)))


def flat(c: str, bg: str) -> str:
    """A colour with alpha, blended onto the background (terminals have no alpha)."""
    r, g, b, a = rgba(c)
    return c[:7] if a >= 1 else mix(bg, hexc(r, g, b), a)


def luminance(c: str) -> float:
    r, g, b, _ = rgba(c)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


# --- loading ------------------------------------------------------------------------------------

def merge(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in extra.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def theme_files() -> dict[str, Path]:
    files = {p.stem: p for p in sorted((HERE / "themes").glob("*.json"))}
    files.update({p.stem: p for p in sorted((HERE / "variants").glob("*.json"))})
    return files


def load(name: str) -> dict[str, Any]:
    files = theme_files()
    if name not in files:
        raise SystemExit(f"kiln: no theme {name!r} (have: {', '.join(files)})")
    raw = json.loads(files[name].read_text())
    parent = load(raw["extends"]) if raw.get("extends") else json.loads((HERE / "base.json").read_text())
    t = merge(parent, {k: v for k, v in raw.items() if k != "extends"})
    t["name"] = name
    t["kind"] = "variant" if files[name].parent.name == "variants" else "theme"
    return t


def resolve(t: dict[str, Any], mode: str, solid: bool = True) -> dict[str, str]:
    """Every colour of one mode plus the roles (accent, ok, …); solid = alpha blended onto bg."""
    c = dict(t["modes"][mode])
    if solid:
        c = {k: flat(v, c["bg"]) for k, v in c.items()}
    for role, name in t["semantic"].items():
        c[role] = c[name]
    return c


def glow(t: dict[str, Any], mode: str) -> list[str]:
    g = t.get("glow", {})
    stops = g.get(mode) if isinstance(g, dict) else None
    return stops or [resolve(t, mode)[n] for n in ("blue", "violet", "pink")]


def ansi16(t: dict[str, Any], mode: str) -> list[str]:
    c = resolve(t, mode)
    m = t["ansi"] | (t.get("ansi_light", {}) if mode == "light" else {})
    base = [c[m[n]] for n in ANSI]
    toward = c["ink"] if mode == "dark" else c["bg"]
    bright = [mix(x, toward, 0.28) for x in base]
    bright[0], bright[7] = c[m["bright_black"]], c[m["bright_white"]]
    return base + bright


# --- outputs ------------------------------------------------------------------------------------

def css_vars(t: dict[str, Any], mode: str) -> str:
    c = resolve(t, mode, solid=False)
    lines = [f"--{k}: {v};" for k, v in c.items()]
    stops = glow(t, mode)
    lines.append(f"--glow: linear-gradient(120deg, {', '.join(stops)});")
    lines.append(f"--glow-1: {stops[0]}; --glow-2: {stops[len(stops) // 2]}; --glow-3: {stops[-1]};")
    sky = t.get("sky", {}).get(mode) if isinstance(t.get("sky"), dict) else None
    lines.append(f"--sky: {sky or c['bg']};")
    lines.append(f"--blur: {t.get('translucent', {}).get('blur', 0)}px;")
    lines.append(f"color-scheme: {mode};")
    return " ".join(lines)


def css(t: dict[str, Any], scope: str = ":root") -> str:
    """Dark first; light under prefers-color-scheme and data-theme, the artifact contract."""
    fixed = [f"--mono: {t['font']['mono']};", f"--sans: {t['font']['sans']};"]
    fixed += [f"--r-{k}: {v}px;" for k, v in t["radius"].items()]
    fixed += [f"--s-{k}: {v}px;" for k, v in t["space"].items()]
    dark, light = css_vars(t, "dark"), css_vars(t, "light")
    return (
        f"/* kiln theme {t['name']}, built by agent-kit/design/kiln.py. Edit themes/{t['name']}.json, not this. */\n"
        f"{scope} {{ {' '.join(fixed)} {dark} }}\n"
        f"@media (prefers-color-scheme: light) {{ {scope}:not([data-theme=\"dark\"]) {{ {light} }} }}\n"
        f"{scope}[data-theme=\"light\"] {{ {light} }}\n{scope}[data-theme=\"dark\"] {{ {dark} }}\n"
    )


def ghostty(t: dict[str, Any], mode: str) -> str:
    c = resolve(t, mode)
    lines = [f"# kiln theme {t['name']} ({mode}), built by agent-kit/design/kiln.py"]
    lines += [f"palette = {i}={x}" for i, x in enumerate(ansi16(t, mode))]
    lines += [f"background = {c['bg']}", f"foreground = {c['ink']}", f"cursor-color = {c['cursor']}",
              f"cursor-text = {c['bg']}", f"selection-background = {c['selection']}",
              f"selection-foreground = {c['ink']}"]
    if tr := t.get("translucent"):
        lines += [f"background-opacity = {tr.get('opacity', 1)}", f"background-blur = {tr.get('blur', 0)}"]
    return "\n".join(lines) + "\n"


def herdr(t: dict[str, Any]) -> str:
    out = [f"# kiln theme {t['name']} for herdr (agent-kit/design/kiln.py): paste below your [theme] table.",
           "# [theme.custom] always applies; [theme.custom.light] only with theme.auto_switch = true."]
    for mode, table in (("dark", "theme.custom"), ("light", "theme.custom.light")):
        c = resolve(t, mode)
        out.append(f"\n[{table}]")
        out += [f'{key} = "{c[name]}"' for key, name in HERDR.items()]
    return "\n".join(out) + "\n"


def starship(t: dict[str, Any]) -> str:
    c, g = resolve(t, "dark"), t["glyphs"]
    pal = "\n".join(f'{k} = "{v}"' for k, v in c.items())
    return f"""# kiln theme {t['name']} for starship (agent-kit/design/kiln.py). Copy to ~/.config/starship.toml,
# or keep yours and take only [palettes.kiln] and `palette`.
palette = "kiln"
format = "$directory$git_branch$git_status$python$nodejs$env_var$cmd_duration$line_break$character"

[directory]
style = "bold ink"
truncation_length = 3

[git_branch]
format = "[{g['sep']} $branch]($style) "
style = "muted"

[git_status]
format = "[$all_status$ahead_behind]($style) "
style = "warn"

[python]
format = "[{g['sep']} py $version]($style) "
style = "faint"

[nodejs]
format = "[{g['sep']} node $version]($style) "
style = "faint"

[env_var.AP_PROFILE]
format = "[{g['dot']} $env_value]($style) "
style = "bold accent"

[cmd_duration]
format = "[{g['sep']} $duration]($style) "
style = "faint"

[character]
success_symbol = "[{g['prompt']}](bold accent)"
error_symbol = "[{g['prompt']}](bold err)"

[palettes.kiln]
{pal}
"""


def gemini(t: dict[str, Any], mode: str) -> str:
    c = resolve(t, mode)
    theme = {
        "name": f"kiln-{t['name']}" + ("-light" if mode == "light" else ""), "type": "custom",
        "background": {"primary": c["bg"], "diff": {"added": mix(c["bg"], c["green"], 0.22),
                                                   "removed": mix(c["bg"], c["red"], 0.22)}},
        "text": {"primary": c["ink"], "secondary": c["muted"], "link": c["link"], "accent": c["accent"],
                 "response": c["ink"]},
        "border": {"default": c["line"]},
        "status": {"success": c["ok"], "warning": c["warn"], "error": c["err"]},
        "ui": {"comment": c["faint"], "symbol": c["soft"], "active": c["accent"], "focus": c["info"],
               "gradient": glow(t, mode)},
    }
    return json.dumps(theme, indent=2) + "\n"


def lua(t: dict[str, Any]) -> str:
    def rgb(h: str) -> str:
        r, g, b, _ = rgba(h)
        return f"{{ red = {r / 255:.3f}, green = {g / 255:.3f}, blue = {b / 255:.3f} }}"

    out = [f"-- kiln theme {t['name']} for Hammerspoon, built by agent-kit/design/kiln.py.", "return {"]
    out.append(f'  name = "{t["name"]}",')
    out.append(f'  font = {{ mono = "{t["font"]["mono_name"]}" }},')
    out.append(f"  opacity = {t.get('translucent', {}).get('opacity', 0.95)},")
    for mode in MODES:
        c = resolve(t, mode)
        out.append(f"  {mode} = {{")
        out += [f"    {k} = {rgb(v)}," for k, v in c.items()]
        out.append(f"    glow = {{ {', '.join(rgb(s) for s in glow(t, mode))} }},")
        out.append("  },")
    out.append("}")
    return "\n".join(out) + "\n"


def shell(t: dict[str, Any]) -> str:
    """The glow for shell scripts (design/kiln.sh reads ~/.config/kiln/theme.sh), alpha blended."""
    out = [f"# kiln theme {t['name']} for shell scripts (design/kiln.sh), built by agent-kit/design/kiln.py.",
           f"KILN_THEME={t['name']}"]
    for mode in MODES:
        bg = resolve(t, mode)["bg"]
        out.append(f'KILN_GLOW_{mode.upper()}="{" ".join(flat(s, bg) for s in glow(t, mode))}"')
    return "\n".join(out) + "\n"


def flat_json(t: dict[str, Any]) -> str:
    out = {k: t[k] for k in ("name", "label", "about", "font", "radius", "space", "semantic", "glyphs") if k in t}
    out["colors"] = {m: resolve(t, m) for m in MODES}
    out["raw"] = {m: resolve(t, m, solid=False) for m in MODES}
    out["glow"] = {m: glow(t, m) for m in MODES}
    out["ansi16"] = {m: ansi16(t, m) for m in MODES}
    out["translucent"] = t.get("translucent")
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def preview(themes: list[dict[str, Any]], active: str) -> str:
    """The specimen page; with several themes, a picker switches between them (data-kiln)."""
    style = css(next(t for t in themes if t["name"] == active))
    style += "".join(css(t, f':root[data-kiln="{t["name"]}"]') for t in themes)
    style += (HERE / "components.css").read_text()
    meta = [{"name": t["name"], "label": t.get("label", t["name"]), "about": t.get("about", "")} for t in themes]
    page = (HERE / "preview.html").read_text()
    return (page.replace("/*STYLE*/", style).replace("/*THEMES*/", json.dumps(meta, ensure_ascii=False))
            .replace("{{active}}", active))


def outputs(t: dict[str, Any]) -> dict[str, str]:
    return {
        "tokens.css": css(t), "components.css": (HERE / "components.css").read_text(),
        "ghostty/dark": ghostty(t, "dark"), "ghostty/light": ghostty(t, "light"),
        "herdr.toml": herdr(t), "starship.toml": starship(t),
        "gemini.json": gemini(t, "dark"), "gemini-light.json": gemini(t, "light"),
        "theme.lua": lua(t), "theme.sh": shell(t), "theme.json": flat_json(t), "preview.html": preview([t], t["name"]),
    }


def build(check: bool = False) -> int:
    themes = [load(n) for n in theme_files()]
    want: dict[Path, str] = {}
    for t in themes:
        want.update({DIST / t["name"] / rel: text for rel, text in outputs(t).items()})
    real = [t for t in themes if t["kind"] == "theme"]
    want[DIST / "gallery.html"] = preview(real, "kiln" if any(t["name"] == "kiln" for t in real) else real[0]["name"])
    want[DIST / "index.json"] = json.dumps(
        [{"name": t["name"], "label": t.get("label", t["name"]), "kind": t["kind"], "about": t.get("about", "")}
         for t in themes], indent=2, ensure_ascii=False) + "\n"
    if check:
        stale = [str(p.relative_to(HERE)) for p, text in want.items() if not p.exists() or p.read_text() != text]
        known = set(want)
        extra = [str(p.relative_to(HERE)) for p in DIST.rglob("*") if p.is_file() and p not in known]
        if stale or extra:
            _ui(sys.stderr).line("err", "dist/ is stale", "run: design/kiln.py build")
            print("    " + "\n    ".join(stale + extra), file=sys.stderr)
            return 1
        return 0
    for p, text in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    for p in DIST.rglob("*"):  # drop files of removed themes
        if p.is_file() and p not in want:
            p.unlink()
    _ui().line("ok", f"built {len(themes)} themes", str(DIST.relative_to(HERE.parent)))
    return 0


# --- switching ----------------------------------------------------------------------------------

def link(src: Path, dst: Path) -> None:
    if dst.exists() and not dst.is_symlink():
        _ui(sys.stderr).line("warn", f"skipped {dst}", "a real file, not a link; move it away and run kiln use")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)


HERDR_BEGIN = "# >>> kiln: `kiln use` and `kiln lightswitch` rewrite this block >>>"
HERDR_END = "# <<< kiln <<<"


def herdr_block(t: dict[str, Any], mode: str) -> str:
    """herdr's [theme] tables for a theme and mode; herdr has no include, so kiln writes them in place."""
    lines = [HERDR_BEGIN, "[theme]", 'name = "tokyo-night"   # base only; kiln overrides every colour token',
             f"auto_switch = {'true' if mode == 'auto' else 'false'}",
             'dark_name = "tokyo-night"', 'light_name = "tokyo-night"']
    tables = [("theme.custom", "light" if mode == "light" else "dark")]
    if mode == "auto":
        tables.append(("theme.custom.light", "light"))
    for table, m in tables:
        c = resolve(t, m)
        lines += ["", f"[{table}]"] + [f'{key} = "{c[name]}"' for key, name in HERDR.items()]
    return "\n".join(lines + [HERDR_END])


Note = tuple[str, str, str, str]  # role (ok, warn), tool, what happened, how to pick it up


def write_herdr(name: str, mode: str) -> Note | None:
    """Rewrite the kiln block in herdr's config (through the dotfiles link); None if there is none."""
    path = Path(os.environ.get("HERDR_CONFIG_PATH") or CONFIG / "herdr" / "config.toml")
    try:
        text = path.read_text()
    except OSError:
        return None
    if HERDR_BEGIN not in text or HERDR_END not in text:
        return ("warn", "herdr", f"no kiln block in {path}", f"paste {DIST / name / 'herdr.toml'} by hand")
    head, rest = text.split(HERDR_BEGIN, 1)
    tail = rest.split(HERDR_END, 1)[1]
    new = head + herdr_block(load(name), mode) + tail
    if new != text:
        path.resolve().write_text(new)
    return ("ok", "herdr", "theme written", "prefix+shift+r reloads it")


def write_opencode(mode: str) -> Note | None:
    """opencode's `system` theme draws with the terminal's palette, which is the kiln theme in Ghostty."""
    folder = CONFIG / "opencode"
    if not folder.is_dir():
        return None
    path = folder / "cli.json"
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
    except ValueError:
        return ("warn", "opencode", f"{path} is not valid JSON", "left alone")
    want = {"name": "system", "mode": "system" if mode == "auto" else mode}
    if data.get("theme") != want:
        data["theme"] = want
        path.write_text(json.dumps(data, indent=2) + "\n")
    return ("ok", "opencode", "system theme, draws with the terminal's kiln colours", "restart opencode")


def current() -> str | None:
    p = CONFIG / "kiln"
    return p.resolve().name if p.is_symlink() else None


PINS = ("auto", "dark", "light")


def current_mode() -> str:
    """dark, light or auto (follow macOS); kept in ~/.config/kiln-mode, read by ap and the widget too."""
    try:
        m = (CONFIG / "kiln-mode").read_text().strip()
    except OSError:
        return "auto"
    return m if m in PINS else "auto"


def use(name: str | None, mode: str | None = None) -> int:
    """Point ~/.config/kiln at a theme; Ghostty's kiln-current themes follow through that link.

    mode dark or light pins every tool to that mode: both Ghostty kiln-current names point at it,
    and ap and the widget read ~/.config/kiln-mode. auto follows macOS. None keeps the last one."""
    name = name or current() or "kiln"
    mode = mode or current_mode()
    if not (DIST / name).is_dir():
        raise SystemExit(f"kiln: no built theme {name!r}; kiln list shows them")
    link(DIST / name, CONFIG / "kiln")
    (CONFIG / "kiln-mode").write_text(mode + "\n")
    themes = CONFIG / "ghostty" / "themes"
    dark = "light" if mode == "light" else "dark"
    light = "dark" if mode == "dark" else "light"
    link(CONFIG / "kiln" / "ghostty" / dark, themes / "kiln-current")
    link(CONFIG / "kiln" / "ghostty" / light, themes / "kiln-current-light")
    for t in theme_files():  # every theme also by its own name, to try one in Ghostty directly
        if (DIST / t).is_dir():
            base = "kiln" if t == "kiln" else f"kiln-{t}"
            link(DIST / t / "ghostty" / "dark", themes / base)
            link(DIST / t / "ghostty" / "light", themes / f"{base}-light")
    shown = "follows macOS" if mode == "auto" else f"always {mode}"
    ui = _ui()
    ui.title("kiln", f"{name} {ui.g('sep')} {shown}")
    ui.line("ok", "theme linked", "cmd+shift+, reloads it", tool="Ghostty")
    for note in (write_herdr(name, mode), write_opencode(mode)):
        if note:
            ui.line(note[0], note[2], note[3], tool=note[1])
    ui.line("ok", "follow it now", tool="ap, pages")
    ui.line("info", "reload Hammerspoon", "it reads the theme when it starts", tool="widget")
    print(file=ui.stream)
    return 0


def macos_mode() -> str:
    """What macOS shows now: dark or light (read from its preferences plist, no subprocess)."""
    try:
        with (Path.home() / "Library/Preferences/.GlobalPreferences.plist").open("rb") as f:
            return "dark" if plistlib.load(f).get("AppleInterfaceStyle") == "Dark" else "light"
    except (OSError, plistlib.InvalidFileException, ValueError):
        return "dark"


def lightswitch(to: str | None) -> int:
    """Flip every tool between dark and light (or pin one, or `auto` to follow macOS again)."""
    if to is None:
        now = current_mode()
        to = "light" if (macos_mode() if now == "auto" else now) == "dark" else "dark"
    return use(None, to)


def listing() -> int:
    cur = current()
    ui = _ui()
    mode = current_mode()
    ui.title("kiln", f"themes {ui.g('sep')} " + ("follow macOS" if mode == "auto" else f"always {mode}"))
    for n in theme_files():
        t = load(n)
        mark = ui.fade(ui.g("dot"), 0.5, 0.5) if n == cur else " "
        kind = " (variant of " + json.loads(theme_files()[n].read_text())["extends"] + ")" if t["kind"] == "variant" else ""
        name = ui.fade(f"{n:14}") if n == cur else ui.c(f"{n:14}", "bold")
        print(f"  {mark} {name} {ui.c(t.get('about', '') + kind, 'faint')}")
    print()
    for cmd, what in (("kiln use <theme>", "switch"), ("kiln lightswitch", "dark or light everywhere"),
                      ("kiln gallery", "every theme on one page")):
        ui.line("info", ui.c(f"{cmd:<17}", "bold"), what)
    print()
    return 0


# --- import -------------------------------------------------------------------------------------

def read_scheme(path: Path, profile: str | None = None) -> dict[str, Any]:
    """bg, fg, selection and 16 ANSI colours from a Ghostty theme or an iTerm2 .itermcolors/prefs plist."""
    data = path.read_bytes()
    if data.lstrip().startswith(b"<?xml") or data.startswith(b"bplist"):
        d = plistlib.loads(data)
        if "New Bookmarks" in d:  # iTerm2 preferences: take a profile
            prof = [b for b in d["New Bookmarks"] if profile in (None, b.get("Name"))]
            if not prof:
                raise SystemExit(f"kiln: no profile {profile!r} in {path}")
            d = prof[0]

        def col(key: str) -> str | None:
            c = d.get(key)
            return hexc(c["Red Component"] * 255, c["Green Component"] * 255, c["Blue Component"] * 255) if c else None

        out = {"bg": col("Background Color"), "fg": col("Foreground Color"), "sel": col("Selection Color"),
               "ansi": [col(f"Ansi {i} Color") for i in range(16)]}
    else:
        out = {"bg": None, "fg": None, "sel": None, "ansi": [None] * 16}
        for line in data.decode().splitlines():
            key, _, val = (s.strip() for s in line.partition("="))
            if key == "palette":
                i, _, c = val.partition("=")
                out["ansi"][int(i)] = "#" + c.strip().lstrip("#")[:6]
            elif key in ("background", "foreground", "selection-background"):
                out[{"background": "bg", "foreground": "fg", "selection-background": "sel"}[key]] = \
                    "#" + val.lstrip("#")[:6]
    if not out["bg"] or not out["fg"] or None in out["ansi"]:
        raise SystemExit(f"kiln: {path} lacks a background, foreground or one of the 16 colours")
    return out


def palette(s: dict[str, Any]) -> dict[str, str]:
    bg, fg, a = s["bg"], s["fg"], s["ansi"]
    return {
        "bg": bg, "surface": mix(bg, fg, 0.035), "raised": mix(bg, fg, 0.08), "line": mix(bg, fg, 0.16),
        "ink": fg, "soft": mix(fg, bg, 0.2), "muted": mix(fg, bg, 0.45), "faint": mix(fg, bg, 0.62),
        "red": a[1], "green": a[2], "amber": a[3], "blue": a[4], "violet": a[5], "cyan": a[6], "pink": a[13],
        "selection": s["sel"] or mix(bg, a[5], 0.25),
    }


GHOSTTY_THEMES = (Path("/Applications/Ghostty.app/Contents/Resources/ghostty/themes"),
                  Path("/usr/share/ghostty/themes"), CONFIG / "ghostty" / "themes")
ITERM_PREFS = Path.home() / "Library/Preferences/com.googlecode.iterm2.plist"


def installed() -> dict[str, Path]:
    """Ghostty themes on this machine (bundled and your own), by name; kiln's own links left out."""
    found: dict[str, Path] = {}
    for d in GHOSTTY_THEMES:
        if d.is_dir():
            for f in sorted(d.iterdir()):
                if f.is_file() and not f.name.startswith("kiln"):
                    found.setdefault(f.name, f)
    return found


def find_scheme(ref: str) -> Path:
    """A file path, an installed Ghostty theme name (any case), or `iterm` for iTerm2's preferences."""
    path = Path(ref).expanduser()
    if path.is_file():
        return path
    if ref.lower() == "iterm" and ITERM_PREFS.is_file():
        return ITERM_PREFS
    by_lower = {n.lower(): p for n, p in installed().items()}
    if ref.lower() in by_lower:
        return by_lower[ref.lower()]
    raise SystemExit(f"kiln: no file or installed theme {ref!r}; kiln installed lists them")


def list_installed() -> int:
    names = list(installed())
    ui = _ui()
    ui.title("kiln", f"{len(names)} Ghostty themes on this machine")
    for n in names:
        print(f"  {ui.c(ui.g('sep'), 'faint')} {n}")
    print()
    ui.line("info", ui.c('kiln import "<name>" --name x', "bold"), "make a kiln theme from one")
    if ITERM_PREFS.is_file():
        profiles = [b.get("Name") for b in plistlib.loads(ITERM_PREFS.read_bytes()).get("New Bookmarks", [])]
        ui.line("info", ui.c('kiln import iterm --profile "<name>" --name x', "bold"),
                "iTerm2 profiles: " + ", ".join(map(str, profiles)))
    return 0


def gallery() -> int:
    page = DIST / "gallery.html"
    print(page)
    if sys.platform == "darwin" and sys.stdout.isatty():
        os.system(f"open '{page}'")
    return 0


def import_theme(args: argparse.Namespace) -> int:
    args.file = str(find_scheme(args.file))
    if args.light:
        args.light = str(find_scheme(args.light))
    first = palette(read_scheme(Path(args.file).expanduser(), args.profile))
    modes = {"dark" if luminance(first["bg"]) < 0.5 else "light": first}
    if args.light:
        modes["light"] = palette(read_scheme(Path(args.light).expanduser(), args.profile))
    only = next(iter(modes.values()))
    for m in MODES:  # a theme with one mode uses it for both
        modes.setdefault(m, only)
    theme = {"name": args.name, "label": args.label or args.name, "about": f"Imported from {Path(args.file).name}.",
             "modes": modes, "glow": {m: [modes[m]["blue"], modes[m]["violet"], modes[m]["pink"]] for m in MODES}}
    out = HERE / "themes" / f"{args.name}.json"
    if out.exists() and not args.force:
        raise SystemExit(f"kiln: {out.name} exists; --force replaces it")
    out.write_text(json.dumps(theme, indent=2) + "\n")
    _ui().line("ok", f"wrote themes/{out.name}", "edit its glow and roles if you like")
    return build()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kiln", description="Themes for every tool in this setup.")
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("build", help="rebuild dist/ from base.json and the themes")
    b.add_argument("--check", action="store_true", help="only check that dist/ is current")
    sub.add_parser("list", help="themes, and which one is in use")
    u = sub.add_parser("use", help="switch theme (default: keep the current one and relink)")
    u.add_argument("name", nargs="?")
    u.add_argument("--mode", choices=PINS, help="dark or light pins every tool to it; auto follows macOS "
                   "(default: keep the last one)")
    ls = sub.add_parser("lightswitch", help="flip every tool between dark and light")
    ls.add_argument("to", nargs="?", choices=PINS, help="dark, light, or auto to follow macOS again "
                    "(default: the other one)")
    sub.add_parser("installed", help="Ghostty themes and iTerm2 profiles on this machine, to import")
    sub.add_parser("gallery", help="open the page with every theme, dark and light")
    i = sub.add_parser("import", help="make a theme from an installed Ghostty theme, a file, or iTerm2")
    i.add_argument("file", help="installed Ghostty theme name (kiln installed), a Ghostty theme file, "
                   ".itermcolors, an iTerm2 preferences plist, or `iterm` for yours")
    i.add_argument("--light", help="a second theme (name or file) for the light mode")
    i.add_argument("--name", required=True, help="theme name, e.g. dracula")
    i.add_argument("--label", help="display name")
    i.add_argument("--profile", help="iTerm2 preferences: profile name (default: the first)")
    i.add_argument("--force", action="store_true", help="replace an existing theme file")
    a = p.parse_args(argv)
    if a.cmd == "build":
        return build(a.check)
    if a.cmd == "use":
        return use(a.name, a.mode)
    if a.cmd == "installed":
        return list_installed()
    if a.cmd == "gallery":
        return gallery()
    if a.cmd == "lightswitch":
        return lightswitch(a.to)
    if a.cmd == "import":
        return import_theme(a)
    return listing()


def run() -> int:
    """main() with errors in the kiln look: one ✗ line on stderr, exit 1."""
    try:
        return main()
    except BrokenPipeError:  # kiln list | head
        return 0
    except SystemExit as e:
        if isinstance(e.code, str):
            _ui(sys.stderr).line("err", e.code.removeprefix("kiln: "))
            return 1
        return e.code if isinstance(e.code, int) else 0


if __name__ == "__main__":
    raise SystemExit(run())
