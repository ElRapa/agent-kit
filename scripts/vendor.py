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
    (out / "UPSTREAM").write_text(
        f"repo: https://github.com/{source['repo']}\ncommit: {source['commit']}\npath: {path}\n"
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
    "decode and run": r"base64\s+(-d|--decode)|eval\s*\(|exec\s*\(",
    "instruction override": r"(?i)ignore (all |any )?(previous|prior|above|earlier) (instructions|rules)",
    "secret access": r"(?i)(\.ssh/|id_rsa|keychain|find-generic-password|\.aws/credentials|\.netrc)",
    "token variable": r"\b[A-Z_]*(TOKEN|API_KEY|SECRET)[A-Z_]*\b",
    "sending data out": r"(?i)(curl|wget|fetch|http)[^\n]*(-d |--data|POST|upload)",
    "turning off safety": r"(?i)(--dangerously|skip-permissions|bypassPermissions|--no-verify|disable[-_ ]?(sandbox|safety))",
    "hook or settings change": r"(?i)(settings\.json|hooks?\.json|\.claude/hooks|PreToolUse|PostToolUse|SessionStart)",
}


def scan() -> int:
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "-U0", "HEAD", "--", "skills", "vendor.toml"],
        check=True, capture_output=True, text=True,
    ).stdout
    new_files = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "skills"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    if DIRECT_DIFF.exists():
        diff += DIRECT_DIFF.read_text()
    added = [line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    for f in new_files:
        try:
            added += (ROOT / f).read_text().splitlines()
        except UnicodeDecodeError:
            print(f"binary file added: {f}")
    hits = [(why, line.strip()[:160]) for line in added for why, rx in RISKY.items() if re.search(rx, line)]
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
                [*git, "diff", old[d["skill"]], d["commit"], "--", d.get("path", d["skill"])],
                check=True, capture_output=True, text=True,
            ).stdout)
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
    return 1 if check and drift else 0


if __name__ == "__main__":
    sys.exit(main())
