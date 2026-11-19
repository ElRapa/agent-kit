"""Copy the third-party skills listed in vendor.toml into skills/, at their pinned commits.

Each copied skill gets the upstream LICENSE and an UPSTREAM file (repo, commit, path).
`--check` changes nothing and exits 1 when skills/ differs from vendor.toml.
`--latest` first moves every pinned commit in vendor.toml to the upstream default branch.
`--scan` checks the lines that the uncommitted vendor changes add for risky patterns; exit 1 on a hit.
`--direct-diff` writes the upstream diff of every [[direct]] pin that moved to .direct.diff (for --scan
and the review).
`--direct` prints the [[direct]] packs as `repo@commit skill` lines for install.sh.
"""

import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
DIRECT_DIFF = ROOT / ".direct.diff"


def fetch(repo: str, commit: str, dest: Path) -> None:
    run = lambda *a: subprocess.run(["git", "-C", str(dest), *a], check=True, capture_output=True)  # noqa: E731
    dest.mkdir()
    run("init", "-q")
    run("fetch", "-q", "--depth", "1", f"https://github.com/{repo}", commit)
    run("checkout", "-q", "FETCH_HEAD")


def build(src: Path, path: str, source: dict, out: Path) -> None:
    shutil.copytree(src / path, out)
    shutil.copy(src / source["license"], out / "LICENSE")
    note = ""
    if out.name in source.get("allow_model_invocation", []):
        # The one change vendor.py makes: agents may start this skill on their own (AGENTS.md routes to it).
        skill = out / "SKILL.md"
        lines = skill.read_text().splitlines(keepends=True)
        skill.write_text("".join(x for x in lines if not x.startswith("disable-model-invocation:")))
        note = "Changed: removed disable-model-invocation (vendor.toml allow_model_invocation).\n"
    (out / "UPSTREAM").write_text(
        f"repo: https://github.com/{source['repo']}\ncommit: {source['commit']}\npath: {path}\n{note}"
        "Vendored by scripts/vendor.py. Do not edit here; change vendor.toml instead.\n"
    )


def same(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    if filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)[1:] != ([], []):
        return False
    return all(same(a / d, b / d) for d in cmp.common_dirs)


RISKY = {
    "download piped to a shell": r"(curl|wget)[^\n|]*\|\s*(ba|z)?sh",
    "decode and run": r"base64\s+(-d|--decode)|\beval\s*\(|\bexec\s*\(",
    # Heuristics only; the Claude review (gate 2) backs them up.
    "instruction override": r"(?i)\b(ignore|disregard|forget|override|bypass)\b[^\n]{0,40}\b(instructions?|rules|guidelines|system prompt|guardrails|AGENTS\.md|CLAUDE\.md)\b",
    "new system prompt": r"(?i)(new|updated|real|true) system prompt|you are no longer|from now on,? you (must|will)",
    "addresses the reviewer": r"(?i)review\.json|pre-?approved|auto-?approv|\b(reviewer|verdict)\b[^\n]{0,40}\b(pass|approved?|merge|safe)\b",
    "secret access": r"(?i)(\.ssh/|id_rsa|keychain|find-generic-password|\.aws/credentials|\.netrc)",
    "token variable": r"\b[A-Z_]*(TOKEN|API_KEY|SECRET)[A-Z_]*\b",
    "sending data out": r"(?i)(curl|wget|fetch|http)[^\n]*(-d |--data|POST|upload)",
    "turning off safety": r"(?i)(--dangerously|skip-permissions|bypassPermissions|--no-verify|disable[-_ ]?(sandbox|safety))",
    "hook or settings change": r"(?i)(settings\.json|hooks?\.json|\.claude/hooks|PreToolUse|PostToolUse|SessionStart)",
}


def added_lines(diff: str) -> list[str]:
    """Added content lines of a unified diff.

    `---`/`+++` are file headers only between a `diff --git` line and that file's first `@@`;
    after an `@@`, every `+` line is content, whatever it starts with.
    """
    out, in_header = [], False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_header = True
        elif line.startswith("@@"):
            in_header = False
        elif in_header and line.startswith(("--- ", "+++ ")):
            continue
        elif not in_header and line.startswith("+"):
            out.append(line[1:])
    return out


def scan() -> int:
    git = ["git", "-C", str(ROOT)]
    paths = ["--", "skills", "vendor.toml"]
    diff = subprocess.run([*git, "diff", "-U0", "HEAD", *paths], check=True, capture_output=True, text=True).stdout
    numstat = subprocess.run([*git, "diff", "--numstat", "HEAD", *paths], check=True, capture_output=True, text=True).stdout
    new_files = subprocess.run(
        [*git, "ls-files", "--others", "--exclude-standard", "skills"], check=True, capture_output=True, text=True
    ).stdout.split()
    if DIRECT_DIFF.exists():
        diff += DIRECT_DIFF.read_text()
    added = added_lines(diff)
    # Binary changes have no text to scan, so they always need a person.
    hits = [("binary file changed", row.split("\t")[-1]) for row in numstat.splitlines() if row.startswith("-\t-\t")]
    for f in new_files:
        try:
            added += (ROOT / f).read_text().splitlines()
        except UnicodeDecodeError:
            hits.append(("binary file added", f))
    hits += [(why, line.strip()[:160]) for line in added for why, rx in RISKY.items() if re.search(rx, line)]
    for why, line in hits:
        print(f"{why}: {line}")
    return 1 if hits else 0


def direct_diff() -> None:
    old_toml = subprocess.run(
        ["git", "-C", str(ROOT), "show", "HEAD:vendor.toml"], check=True, capture_output=True, text=True
    ).stdout
    old = {d["skill"]: d["commit"] for d in tomllib.loads(old_toml).get("direct", [])}
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for d in tomllib.loads((ROOT / "vendor.toml").read_text()).get("direct", []):
            if old.get(d["skill"], d["commit"]) == d["commit"]:
                continue
            repo = Path(tmp) / d["skill"]
            fetch(d["repo"], d["commit"], repo)
            git = ["git", "-C", str(repo)]
            url = f"https://github.com/{d['repo']}"
            subprocess.run([*git, "fetch", "-q", "--depth", "1", url, old[d["skill"]]], check=True)
            out.append(f"### {d['repo']} {old[d['skill']][:7]}..{d['commit'][:7]} ({d['skill']})\n")
            out.append(subprocess.run(
                [*git, "diff", old[d["skill"]], d["commit"], "--", d["path"]],
                check=True, capture_output=True, text=True,
            ).stdout)
            if not (repo / d["path"] / "SKILL.md").exists():
                sys.exit(f"{d['repo']}: {d['path']}/SKILL.md is gone at {d['commit'][:7]}; set path in vendor.toml")
    DIRECT_DIFF.write_text("".join(out))


def bump(toml: Path) -> None:
    text = toml.read_text()
    data = tomllib.loads(text)
    for source in data["source"] + data.get("direct", []):
        url = f"https://github.com/{source['repo']}"
        out = subprocess.run(["git", "ls-remote", url, "HEAD"], check=True, capture_output=True, text=True)
        head = out.stdout.split()[0]
        if head != source["commit"]:
            text = re.sub(source["commit"], head, text)
            print(f"bumped: {source['repo']} {source['commit'][:7]} -> {head[:7]}")
    toml.write_text(text)


def main() -> int:
    check = "--check" in sys.argv
    if "--scan" in sys.argv:
        return scan()
    if "--direct-diff" in sys.argv:
        direct_diff()
        return 0
    if "--direct" in sys.argv:
        for d in tomllib.loads((ROOT / "vendor.toml").read_text()).get("direct", []):
            print(f"{d['repo']}@{d['commit']} {d['skill']}")
        return 0
    if "--latest" in sys.argv:
        bump(ROOT / "vendor.toml")
    sources = tomllib.loads((ROOT / "vendor.toml").read_text())["source"]
    clones: dict[tuple[str, str], Path] = {}
    drift = []
    with tempfile.TemporaryDirectory() as tmp:
        for source in sources:
            key = (source["repo"], source["commit"])
            if key not in clones:
                clones[key] = Path(tmp) / f"src{len(clones)}"
                fetch(*key, clones[key])
            for path in source["skills"]:
                name = Path(path).name
                fresh = Path(tmp) / "out" / name
                build(clones[key], path, source, fresh)
                target = SKILLS / name
                if target.exists() and same(fresh, target):
                    continue
                drift.append(name)
                if not check:
                    shutil.rmtree(target, ignore_errors=True)
                    shutil.copytree(fresh, target)
    for name in drift:
        print(f"{'differs' if check else 'updated'}: skills/{name}")
    # A vendored skill (it has UPSTREAM) that vendor.toml no longer lists is stale.
    listed = {Path(path).name for source in sources for path in source["skills"]}
    for up in sorted(SKILLS.glob("*/UPSTREAM")):
        if up.parent.name in listed:
            continue
        drift.append(up.parent.name)
        print(f"{'not in vendor.toml' if check else 'removed'}: skills/{up.parent.name}")
        if not check:
            shutil.rmtree(up.parent)
    return 1 if check and drift else 0


if __name__ == "__main__":
    sys.exit(main())
