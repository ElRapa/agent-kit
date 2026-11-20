# Global agent rules

Rules for every project and every harness. Projects add their own AGENTS.md on top.

- Links to something running on this machine (a preview, a dashboard): give a Tailscale link
  (`tailscale serve --bg --https=<port> <port>`), never `localhost`, and open it once yourself first.
  (A `localhost` inside a script template or example is a placeholder, not a link; leave it.)
- Notes: read only the vault in `$AP_VAULT` (the loaded context's vault). Never copy content between vaults.
- Secrets: never print, log or commit a key. Ask for it by name; it lives in the keychain.
- Paths: use `~/…` or repo-relative paths, never `/Users/<name>/…`.
- Docs: a change updates the docs it makes wrong, in the same commit: README.md for people,
  AGENTS.md for agents.
- Look: pages, reports and terminal output you build for the owner use the kiln tokens
  (`~/.config/kiln/tokens.css` and `components.css`, colours by role) unless the project has its own.

## Skills: which one when

Code is written the **ponytail** way (level full) unless the project says otherwise. Prose (docs, PR
text, commit messages) goes through **unslop**. Then pick by situation; a project's own skills win.

Pick skills yourself; the owner does not name them. When you use one, say so in one line with the
reason ("Using data-pipeline-review: this job appends without a key"), so the owner learns them by
use. When the owner asks which skill fits, or seems not to know one exists, use **kit-help**.

[archify explainer: proactive] A plan, comparison, decision, diagnosis or review that needs a table,
steps or several sections also gets a one-page **archify** explainer; a system or flow to understand
gets an archify diagram. Short answers stay in chat. Give a link the owner can open: a file path on
this machine, or a Tailscale link when the owner is elsewhere.

| Situation | Skills, in order |
|---|---|
| Rough idea, side project, customer ask without a spec | idea-to-mvp (grilling only when asked to stress-test) |
| Hard bug, flaky test, regression | diagnosing-bugs, then verify-this for the fix |
| Review before merge | ponytail-review; add blast-radius when the diff is small but risky |
| Large or risky PR, one-way-door design | change-by-change-review or council |
| Harsh structure review, on request | thermo-nuclear-code-quality-review |
| Whole repo health | ponytail-audit |
| Pipeline, dbt, SQL, ingestion | data-pipeline-review (with ponytail-review) |
| LLM feature, prompt, agent, RAG | ai-feature-review |
| Explain a system, flow, schema or plan to a person | archify (diagram or one-page explainer) |
| Session ends, work continues elsewhere | handoff |
| Reflect on how I work with agents, unused skills | ai-loop |
| Which skill fits? | kit-help |

A skill that names another skill that is not installed (for example `arena`): use **council** for
multi-model work and skip the rest.

## Your environment

- `ap env` set it up for this folder's context: `$AP_PROFILE` (e.g. `work-eco`), `$AP_CONTEXT`,
  `$AP_TIER`. Stay inside that context: no providers, vaults or accounts of another one.
- Handing work to another model: `ap resolve "$AP_PROFILE"` lists the model per role;
  `ap exec <harness> --role <role> "<task>"` runs one headless with the same rules.
- `gh` already points at the context's host (`$GH_HOST`) and login; don't pass tokens.
