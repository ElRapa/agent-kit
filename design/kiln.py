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
from typing import Any

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
        "theme.lua": lua(t), "theme.json": flat_json(t), "preview.html": preview([t], t["name"]),
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
            print("kiln: dist/ is stale, run design/kiln.py build:\n  " + "\n  ".join(stale + extra))
            return 1
        return 0
    for p, text in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    for p in DIST.rglob("*"):  # drop files of removed themes
        if p.is_file() and p not in want:
            p.unlink()
    print(f"kiln: built {len(themes)} themes into {DIST.relative_to(HERE.parent)}")
    return 0


# --- switching ----------------------------------------------------------------------------------

def link(src: Path, dst: Path) -> None:
    if dst.exists() and not dst.is_symlink():
        print(f"kiln: skip {dst}: a real file, not a link", file=sys.stderr)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink():
        dst.unlink()
    dst.symlink_to(src)


def current() -> str | None:
    p = CONFIG / "kiln"
    return p.resolve().name if p.is_symlink() else None


def use(name: str | None) -> int:
    """Point ~/.config/kiln at a theme; Ghostty's kiln-current themes follow through that link."""
    name = name or current() or "kiln"
    if not (DIST / name).is_dir():
        raise SystemExit(f"kiln: no built theme {name!r}; kiln list shows them")
    link(DIST / name, CONFIG / "kiln")
    themes = CONFIG / "ghostty" / "themes"
    link(CONFIG / "kiln" / "ghostty" / "dark", themes / "kiln-current")
    link(CONFIG / "kiln" / "ghostty" / "light", themes / "kiln-current-light")
    for t in theme_files():  # every theme also by its own name, to try one in Ghostty directly
        if (DIST / t).is_dir():
            base = "kiln" if t == "kiln" else f"kiln-{t}"
            link(DIST / t / "ghostty" / "dark", themes / base)
            link(DIST / t / "ghostty" / "light", themes / f"{base}-light")
    print(f"kiln: using {name}. Ghostty: cmd+shift+, to reload. Widget: reload Hammerspoon.\n"
          f"herdr: paste {DIST / name / 'herdr.toml'} into its config (no include there).")
    return 0


def listing() -> int:
    cur = current()
    for n in theme_files():
        t = load(n)
        mark = "●" if n == cur else " "
        kind = " (variant of " + json.loads(theme_files()[n].read_text())["extends"] + ")" if t["kind"] == "variant" else ""
        print(f"{mark} {n:14} {t.get('about', '')}{kind}")
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


def import_theme(args: argparse.Namespace) -> int:
    first = palette(read_scheme(Path(args.file).expanduser(), args.profile))
    modes = {"dark" if luminance(first["bg"]) < 0.5 else "light": first}
    if args.light:
        modes["light"] = palette(read_scheme(Path(args.light).expanduser(), args.profile))
    for m in MODES:  # a theme with one mode uses it for both
        modes.setdefault(m, modes["light" if m == "dark" else "dark"])
    theme = {"name": args.name, "label": args.label or args.name, "about": f"Imported from {Path(args.file).name}.",
             "modes": modes, "glow": {m: [modes[m]["blue"], modes[m]["violet"], modes[m]["pink"]] for m in MODES}}
    out = HERE / "themes" / f"{args.name}.json"
    if out.exists() and not args.force:
        raise SystemExit(f"kiln: {out.name} exists; --force replaces it")
    out.write_text(json.dumps(theme, indent=2) + "\n")
    print(f"kiln: wrote themes/{out.name}; edit its glow and roles if you like")
    return build()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kiln", description="Themes for every tool in this setup.")
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("build", help="rebuild dist/ from base.json and the themes")
    b.add_argument("--check", action="store_true", help="only check that dist/ is current")
    sub.add_parser("list", help="themes, and which one is in use")
    u = sub.add_parser("use", help="switch theme (default: keep the current one and relink)")
    u.add_argument("name", nargs="?")
    i = sub.add_parser("import", help="make a theme from a Ghostty theme or an iTerm2 plist")
    i.add_argument("file", help="Ghostty theme file, .itermcolors, or iTerm2 preferences plist")
    i.add_argument("--light", help="a second file for the light mode")
    i.add_argument("--name", required=True, help="theme name, e.g. dracula")
    i.add_argument("--label", help="display name")
    i.add_argument("--profile", help="iTerm2 preferences: profile name (default: the first)")
    i.add_argument("--force", action="store_true", help="replace an existing theme file")
    a = p.parse_args(argv)
    if a.cmd == "build":
        return build(a.check)
    if a.cmd == "use":
        return use(a.name)
    if a.cmd == "import":
        return import_theme(a)
    return listing()


if __name__ == "__main__":
    raise SystemExit(main())
