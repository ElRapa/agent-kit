# agent-kit

Skills, agents and rules I use in every project, for any harness. Plain files in open formats:
`SKILL.md` folders ([Agent Skills](https://agentskills.io)) and `AGENTS.md`. Nothing personal and no
employer or customer names: those live in my private `my-setup/kit-private`.

| Path | What | Read by |
|---|---|---|
| `AGENTS.md` | global rules | Codex, opencode, Copilot; Claude Code when a project has no `CLAUDE.md` |
| `skills/<name>/SKILL.md` | skills | Claude Code, Codex, opencode, Copilot, Gemini CLI, … |
| `agents/opencode/*.md` | subagents in opencode format | opencode, OmO |
| `.claude-plugin/` | the same skills as a Claude Code plugin marketplace | Claude Code `/plugin` |
| `vendor.toml`, `scripts/vendor.py` | third-party skills, pinned, and the script that copies them | you, CI |
| `install.sh` | installs this kit and the private kit for every harness | you, dotfiles |
| `shell/auto-update.zsh` | daily background pull and reinstall | dotfiles `.zshrc` |
| `design/` | kiln, the shared look: five themes (kiln, nightsky, Tokyo Night, Catppuccin, Gruvbox), each building Ghostty, herdr, starship, Gemini CLI, page and widget files; `kiln use <theme>` switches, `kiln import` adds any Ghostty or iTerm2 theme ([design/README.md](design/README.md)) | `install.sh` (puts `kiln` on the PATH), dotfiles, agent-stack, nowu |

## Install and update

```bash
~/code/agent-kit/install.sh          # this kit + my-setup/kit-private, for every harness it finds
~/code/agent-kit/install.sh --pull   # git pull first, then reinstall (the update path)
/plugin marketplace add ElRapa/agent-kit    # inside Claude Code, if you prefer plugins
```

`install.sh` also puts `kiln` on the PATH and links the theme in use into `~/.config/kiln` and
`~/.config/ghostty/themes` (`kiln use <theme>` switches). It runs `npx skills add <folder> -g -y --skill '*'` (vercel-labs/skills, telemetry off),
then the `[[direct]]` packs from `vendor.toml` at their pinned commit. It copies every skill to
`~/.agents/skills` and links each harness (Claude Code, Codex, opencode, Copilot, …) to that copy.
dotfiles' `install.sh` calls it on a new machine.

After that it runs itself: `shell/auto-update.zsh` (sourced by dotfiles' `.zshrc`) fast-forwards
`main` to `origin/main` once a day in the background, only when `main` is checked out, and reruns
`install.sh` when something changed. The `skills` CLI itself is pinned in `install.sh`
(`SKILLS_CLI`), because it runs outside the vendor gates; bump it by hand. Log:
`~/.cache/agent-kit/update.log`; off with `AGENT_KIT_AUTO_UPDATE=0`.

## How you find the right skill

You don't have to. Agents pick skills from their descriptions and from the table in
[AGENTS.md](AGENTS.md), and say in one line which skill they use and why, so you learn them by use.
Ask "which skill fits …?" (or `/kit-help`) when you want to know. Once in a while, `ai-loop` counts
which skills ran and proposes removing the ones nobody uses.

## Skills

Which skill to use in which situation is in [AGENTS.md](AGENTS.md), so every agent reads it too.

| Skill | What | From |
|---|---|---|
| ponytail | default coding style: the smallest complete change, never cut validation or security | ponytail |
| ponytail-review | review a change: bug, risk, scale, missing test, speed, lean | ponytail |
| ponytail-audit | the same checks on a whole repo, ranked | ponytail |
| change-by-change-review | split a big diff into logical units, judge each | own |
| blast-radius | what a change breaks outside the diff, with one proven fact | pstack |
| thermo-nuclear-code-quality-review | very strict structure review, only when asked | cursor-team-kit |
| verify-this | prove a claim with before/after evidence | cursor-team-kit |
| diagnosing-bugs | hard bugs: build a pass/fail loop, then bisect and test hypotheses | mattpocock |
| council | the same question to three models of different providers, merged | own |
| idea-to-mvp | rough idea → one-screen brief → smallest thing that tests the riskiest part | own |
| grilling | interview me about a plan until nothing is assumed | mattpocock |
| data-pipeline-review | rerun safety, backfill, grain, nulls, schema change, data tests, cost | own |
| ai-feature-review | LLM features: evals first, output contract, injection, cost per task | own |
| unslop | cut AI tells from prose | pstack |
| handoff | write a handoff doc for the next session | mattpocock |
| ai-loop | review my agent sessions for patterns, improvements and unused skills | own |
| kit-help | which skill fits this situation | own |
| archify | diagrams and one-page explainers as checked HTML, from a description or the repo | archify (direct) |

archify is the visual layer between agent and person: AGENTS.md turns on its proactive explainer
mode, so plans, comparisons, reviews and diagnoses also come as one page with the conclusion first.
It needs Node >= 18 and a local Chrome for its browser check. Its own update check is off
(`ARCHIFY_UPDATE_CHECK_DISABLED=1`); updates come through `vendor.toml`.

## Third-party skills (vendored)

Skills from other repos are copied into `skills/` at a pinned commit, with their LICENSE and an
`UPSTREAM` file. Packs too big to copy (`[[direct]]`, now archify) are installed from upstream at a
pinned commit. They are prompts every agent follows, so every update passes two automatic gates.

- `vendor.toml` lists repo, commit and skill folders. Don't edit vendored folders; change the list.
  The one change the script makes: `allow_model_invocation` drops `disable-model-invocation` from the
  named skills (blast-radius, unslop, handoff), because AGENTS.md has agents start them on their own.
  The skill's `UPSTREAM` file says so.
- `python3 scripts/vendor.py` copies them and removes vendored skills no longer listed; `--check`
  fails when `skills/` drifted or holds such a stale skill (CI runs it);
  `--latest` moves every commit to upstream HEAD.
- Weekly, `.github/workflows/vendor-update.yml` runs `--latest`, then two gates: `--scan` (heuristic
  patterns such as piping a download to a shell, reading keys, overriding instructions, text aimed at
  the reviewer, hooks) and a Claude review of the diff (`.github/prompts/vendor-review.md`) that
  treats the files as data and must quote evidence for every changed file. The review runs with only
  its own credential, may read only the checkout and write only `review.json`, and its text is never
  published: the PR shows the pins, the changed files, the scan output and pass or hold. The job fails
  if anything outside `skills/` and `vendor.toml` changed. A `[[direct]]` pack whose
  `path` disappears upstream fails the run instead of passing with an empty diff. Both pass: the PR merges by itself and the
  machines pick it up the next day. Protect `main` on GitHub (changes only through PRs), because the
  daily auto-update trusts whatever is on `origin/main`. Either fails: the PR stays open with the label `hold` and the
  reasons; that is the only time you need to look. Needs the secret `CLAUDE_CODE_OAUTH_TOKEN`.
- Known exception: `diagnosing-bugs/scripts/hitl-loop.template.sh` uses a `localhost` URL as an
  example. AGENTS.md treats a `localhost` in a template as a placeholder, not a link.
- New pack: add a `[[source]]` block with only the skills worth having, run the script, add a row
  above and a line in the AGENTS.md table.

Looked at and left out (2026-11): pstack's `poteto-mode` and principles (Cursor-centric, overlaps OmO's
orchestration), superpowers (strong but forces itself on every task), tstack (`council` idea taken,
the rest is T3 Code and GitHub specific), karpathy-guidelines (ponytail covers it), ECC (1,000+
skills, too broad), diagram-design (archify covers it and checks its output).

Per project: commit the project's own `AGENTS.md` and `.agents/skills/`, so cloud agents get them too.

## Layers

1. Global: this repo.
2. Per context: `my-setup/kit-private` (private), or a pack of the employer's.
3. Per project: the project's own `AGENTS.md` and skills.
