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

## Install

```bash
npx skills add ~/code/agent-kit -g          # every harness it finds (or: npx skills add ElRapa/agent-kit -g)
npx skills add ~/code/my-setup/kit-private -g   # my private skills, on my machines only
/plugin marketplace add ElRapa/agent-kit    # inside Claude Code, if you prefer plugins
```

Per project: commit the project's own `AGENTS.md` and `.agents/skills/`, so cloud agents get them too.

## Layers

1. Global: this repo.
2. Per context: `my-setup/kit-private` (private), or a pack of the employer's.
3. Per project: the project's own `AGENTS.md` and skills.
