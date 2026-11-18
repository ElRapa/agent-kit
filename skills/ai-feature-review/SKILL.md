---
name: ai-feature-review
description: Review or plan a feature built on an LLM (prompt, agent, RAG, tool calling, extraction, classification) for quality, cost, safety and failure handling. Use for "review my prompt", "is this agent production ready", "add an LLM to", "why does the model sometimes", evals.
---

# AI feature review

An LLM feature is a function that is right most of the time. The review asks: how often, how do we
know, what does it cost, and what happens on the bad runs.

## Check

1. **Evals before tuning.** There is a set of real inputs (20 to 100 is enough to start) with the
   expected output or a grading rule, and a command that scores it. No eval set: build one first from
   real examples, then change the prompt. A prompt change without a before/after score is a guess.
2. **The task is the right size for a model.** Parts that are deterministic (parsing, math, lookups,
   routing on a fixed field) are plain code, not prompt text.
3. **Output contract.** Structured output (JSON schema, tool call) is validated in code; invalid output
   is retried once, then fails loudly or falls back. Free text that code parses with regex is a risk.
4. **Untrusted input.** Text from users, documents, web pages or tool results can carry instructions.
   It is marked as data, and the model's tools and permissions are no wider than the task needs.
   Check what one hostile document could make the agent do.
5. **Retrieval (RAG).** Measure retrieval on its own: for the eval questions, is the right chunk in the
   top k? Bad answers are often bad retrieval, not a bad prompt.
6. **Cost and latency per task.** Tokens in and out per task, times calls per task (agents loop),
   times volume. Is a cheaper model good enough on the eval set? Is caching used for the fixed prefix?
   Use `ap resolve "$AP_PROFILE"` for the model per role instead of naming a model in code.
7. **Failure handling.** Timeouts, rate limits, provider outage, context too long, refusals. Each has a
   defined result for the user.
8. **Observability.** Inputs, outputs, model, prompt version, tokens and cost are logged per call, with
   secrets and personal data removed, so a bad answer can be traced and added to the eval set.

## Report

Each finding names the input that goes wrong, the wrong result, and the fix. Lead with the eval
status: exists or not, and the current score. End with what you did not measure.
