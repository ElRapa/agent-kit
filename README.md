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

## Install and update

```bash
~/code/agent-kit/install.sh          # this kit + my-setup/kit-private, for every harness it finds
~/code/agent-kit/install.sh --pull   # git pull first, then reinstall (the update path)
/plugin marketplace add ElRapa/agent-kit    # inside Claude Code, if you prefer plugins
```

`install.sh` runs `npx skills add <folder> -g -y --skill '*'` (vercel-labs/skills, telemetry off). It
copies every skill to `~/.agents/skills` and links each harness (Claude Code, Codex, opencode, Copilot,
…) to that copy. dotfiles' `install.sh` calls it on a new machine.

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
| ai-loop | review my agent sessions for patterns and improvements | own |

Optional, too big to vendor; install when a project needs it:
`npx skills add cathrynlavery/diagram-design -g` (architecture and other diagrams as HTML/SVG).

## Third-party skills (vendored)

Skills from other repos are copied into `skills/` at a pinned commit, with their LICENSE and an
`UPSTREAM` file. They are prompts every agent follows, so nothing changes without a reviewed diff.

- `vendor.toml` lists repo, commit and skill folders. Don't edit vendored folders; change the list.
- `python3 scripts/vendor.py` copies them; `--check` fails when `skills/` drifted (CI runs it);
  `--latest` moves every commit to upstream HEAD.
- Weekly, `.github/workflows/vendor-update.yml` runs `--latest` and opens a PR. Read the SKILL.md
  diff, merge, then `install.sh --pull` on each machine.
- New pack: add a `[[source]]` block with only the skills worth having, run the script, add a row
  above and a line in the AGENTS.md table.

Looked at and left out (2026-11): pstack's `poteto-mode` and principles (Cursor-centric, overlaps OmO's
orchestration), superpowers (strong but forces itself on every task), tstack (`council` idea taken,
the rest is T3 Code and GitHub specific), karpathy-guidelines (ponytail covers it), ECC (1,000+
skills, too broad), archify (npm toolchain).

Per project: commit the project's own `AGENTS.md` and `.agents/skills/`, so cloud agents get them too.

## Layers

1. Global: this repo.
2. Per context: `my-setup/kit-private` (private), or a pack of the employer's.
3. Per project: the project's own `AGENTS.md` and skills.
