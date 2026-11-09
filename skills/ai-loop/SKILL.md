---
name: ai-loop
description: Review AI coding sessions for recurring work patterns, capabilities, friction, and evidence-backed improvement ideas. Use when asked to run an AI Loop, review OpenCode sessions, or reflect on an individual's or a team's ways of working.
---

# AI Loop

Turn session history into reviewable learning. The purpose is to help an individual understand their work patterns and capabilities, then suggest improvements to their skills, tools, prompts, or workflow. Sessions may also offer useful signals for your team, but any organisation-wide interpretation is a separate, unproven hypothesis that requires explicit consent and clear boundaries.

## Principles

- Run only when explicitly requested; do not schedule scans or continuously monitor sessions.
- Treat sessions as sensitive source material. Inspect only the requested person's sessions and scope; do not share raw transcripts or infer permission to conduct a team-wide review from an individual review.
- Prefer a bounded, representative sample over scanning everything. State the projects, time range, and session count reviewed; ask if the intended scope is unclear.
- Base every finding on specific evidence from the reviewed sessions. Separate observed patterns from interpretations and recommendations; include counterexamples and uncertainty where relevant.
- Do not make silent changes to skills, prompts, configuration, or working habits. Present proposed changes for review and wait for explicit approval before implementing them.
- Avoid reproducing secrets, credentials, client-confidential material, personal data, or unnecessary transcript excerpts in the report. Use short, redacted evidence descriptions.
- Do not use session content to make formal performance, employment, or capability ratings of people. Describe task-specific observed behaviors and possible development opportunities instead.

## OpenCode session discovery

OpenCode's documented macOS/Linux application-data root is `~/.local/share/opencode/`.

- Project-specific session and message data is under `~/.local/share/opencode/project/`.
- For a project inside a Git repository, its storage is associated with that project's slug under `~/.local/share/opencode/project/<project-slug>/storage/`.
- For a project not inside a Git repository, storage is under `~/.local/share/opencode/global/storage/`.
- These are documented locations, not a guarantee that every session lives in one directory. The working project context determines which project data is relevant. Do not recursively inspect all application data or open `auth.json`, logs, or unrelated projects as part of a session review.
- Discover available sessions through `opencode session list` (optionally limit the list with `--max-count`). Use `opencode export <sessionID> --sanitize` when an export is needed; review the sanitized export and avoid retaining it longer than needed.
- Do not delete sessions or modify OpenCode's session database.

When the user asks to review sessions but does not specify scope, ask which project(s) and time range to review, and whether the review is individual-only. Do not assume consent to review other people's sessions or aggregate sessions across a team.

## Review workflow

1. Confirm the review scope: individual, project(s), time period, and whether the user wants a retrospective, skill-improvement suggestions, or both.
2. List sessions with the OpenCode CLI, select a bounded sample within the approved scope, and explain the sample before inspecting transcripts if the selection could surprise the user.
3. Review session content for recurring evidence of:
   - tasks and capabilities the person repeatedly demonstrates;
   - prompts, workflows, or tools that reliably help;
   - repeated corrections, rework, blockers, or unmet needs;
   - skills or reusable instructions that may be missing, unclear, or outdated;
   - changes in approach that appear to improve outcomes.
4. Check whether a pattern recurs across separate sessions. Do not turn a single incident into a general claim. Distinguish direct evidence, interpretation, and unknowns.
5. Report concise findings with the scope and sample size, pattern, redacted evidence, confidence/limitations, and a practical suggested experiment or change.
6. Ask which suggestions the user wants to adopt. Make no edits until the user explicitly approves the specific change and its target.
7. If an approved change is to an OpenCode skill or config, inspect the exact target first, preserve unrelated content, make only the approved change, then reread and verify it. Remind the user to restart OpenCode for config-time changes to load.

## Reporting format

### Scope reviewed
- Project(s), time range, and number of sessions (or state that the review was limited).

### Observed patterns
- **Observation:** what recurs.
- **Evidence:** brief, redacted session references or examples.
- **Interpretation and confidence:** what it may indicate and how strong the evidence is.

### Improvement ideas
- **Proposal:** specific skill, tool, prompt, or workflow change.
- **Expected benefit:** what it may improve.
- **Validation:** a small way to test whether it helps.

### Open questions
- Missing context, counterexamples, or scope limitations.

## Individual learning and the team

Sessions can help an individual reflect on their own working style and capabilities. This does not automatically authorize collection or analysis of colleagues' sessions. Any team-level learning must be explicitly requested, appropriately consented, scoped, and designed to avoid identifying or evaluating individuals. Prefer voluntary, aggregated patterns with evidence limitations made clear; never present session-derived signals as objective performance scores.

## References

- OpenCode storage and session locations: https://opencode.ai/docs/troubleshooting/
- OpenCode session list and sanitized export: https://opencode.ai/docs/cli/
- Inspiration: Cathryn Lavery, “Your First AI Loop Should Be for Yourself”: https://littlemight.com/your-first-ai-loop-should-be-for-yourself/
- Related implementation: https://github.com/cathrynlavery/agent-improvement-loop (repository mentions Claude Code, Codex, and Hermes; do not assume it natively supports OpenCode).
