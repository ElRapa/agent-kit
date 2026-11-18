---
name: council
description: Get the same review or question answered by three models from different providers, then merge what they found. Use for "council", "second opinion", "multi-model review", a one-way-door design choice, or a risky change before merge.
---

# Council

Different models miss different things. A council asks three of them the same question, read only,
and keeps what holds up.

## Pick the members

- Run `ap resolve "$AP_PROFILE" --role <role>` and take the first model of three different providers
  in that role's chain, for the role that fits (`reviewer` for code, `architect` or `oracle` for design). Stay inside the current context:
  no provider the profile does not list.
- If the profile has fewer than three providers, use what it has and say so. Never swap in a provider
  from another context.

## Run

1. Finish what you know first: fix known issues and run the checks, so the council reviews the real
   change and not your to-do list.
2. Write one brief: the goal, the scope (diff, files or design doc), and what to look for. Same brief
   for every member.
3. Start the members in parallel, read only, each with its model named, for example
   `opencode run -m <provider>/<model> "<brief>"`, or the harness's own subagents when they can pick a
   model. (`ap exec` always takes the role's first model, so it gives you one member, not three.)
4. While they run, do not edit the files they read.

## Merge

- Check every finding against the code yourself. Keep it only with a concrete failing case; run it when
  that is cheap (see **verify-this**).
- Merge findings with the same root cause. Note which members found each one.
- Report: kept findings first, then real disagreements between members, then what you dropped and why.
