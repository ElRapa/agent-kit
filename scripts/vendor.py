"""Copy the third-party skills listed in vendor.toml into skills/, at their pinned commits.

Each copied skill gets the upstream LICENSE and an UPSTREAM file (repo, commit, path).
`--check` changes nothing and exits 1 when skills/ differs from vendor.toml.
`--latest` first moves every pinned commit in vendor.toml to the upstream default branch.
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


def bump(toml: Path) -> None:
    text = toml.read_text()
    for source in tomllib.loads(text)["source"]:
        url = f"https://github.com/{source['repo']}"
        out = subprocess.run(["git", "ls-remote", url, "HEAD"], check=True, capture_output=True, text=True)
        head = out.stdout.split()[0]
        if head != source["commit"]:
            text = re.sub(source["commit"], head, text)
            print(f"bumped: {source['repo']} {source['commit'][:7]} -> {head[:7]}")
    toml.write_text(text)


def main() -> int:
    check = "--check" in sys.argv
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
