---
name: idea-to-mvp
description: Turn a rough idea into the smallest working thing that tests it. Use for "I have an idea", "could we build", "what if", "prototype this", a vague feature or side project, or a customer ask that has no spec yet.
---

# Idea to MVP

An idea is a guess about what someone needs. The job is to find the riskiest part of that guess and
build the least that tests it. Work on your own; ask only what you cannot find out.

## 1. Write the brief (one screen)

- **For whom and what pain.** One sentence each. "Me" is a fine user.
- **Done when.** One observable result, such as "I run one command and get the weekly report in my inbox".
- **Riskiest assumption.** The thing that, if false, makes the rest pointless: the data exists, the API
  allows it, the model is good enough, someone wants it.
- **Out of scope.** What you will not build now. Name it so nobody builds it by accident.

Ask the person at most three questions, and only ones whose answer changes what you build. For
everything else, pick the likely answer, write it in the brief as an assumption, and go on.

## 2. Check before you build

- Search for an existing tool, library, API, or a few lines of shell that already do it. If one does,
  say so and stop, or build only the glue.
- Test the riskiest assumption first with a throwaway probe: one API call, one query, one prompt on
  ten real examples. Keep the output; it is evidence.

## 3. Build the smallest version

- One path, end to end, with real data. No auth, settings, UI or deploy unless the brief needs them.
- Follow the **ponytail** skill for the code. Prefer a script or a notebook over an app.
- Put it in a new folder with a `README.md`: what it does, how to run it, the brief, what you skipped.

## 4. Hand back

- What works now, shown with a real run (command and output, or a screenshot).
- What the probe proved or disproved about the riskiest assumption.
- The next step that would teach the most, and what it costs. Not a roadmap.
