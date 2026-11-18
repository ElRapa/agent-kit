---
name: data-pipeline-review
description: Review a data pipeline, ETL/ELT job, dbt model, SQL transform, or ingestion code for the failures that only show up in production data. Use for "review this pipeline", "review this dbt model", "is this SQL safe to run daily", backfills and schema changes.
---

# Data pipeline review

Code review finds wrong code. This review finds right code that breaks on real data, at real
volume, or on the second run. Use **ponytail-review** for the general code checks; this skill adds
the data checks.

## Find out first

- What it reads and writes: tables, files, topics, APIs. Who reads the output downstream.
- How it runs: schedule, trigger, orchestrator, retries, how long a run takes.
- How much data: rows per run, total size, growth. Say which numbers you assumed.

## Check

1. **Rerun safety.** Running it twice for the same period gives the same result. Look for plain
   `INSERT`/append without a key, `MERGE` without a unique key, side effects (emails, API writes) inside
   a retried step.
2. **Backfill.** It can run for any past date, not only "today": no `now()`/`current_date` inside the
   logic, the date comes in as a parameter, late data for old partitions is handled.
3. **Grain and joins.** State the grain of each output (one row per what). A join that can fan out
   (duplicate keys on the right side) or drop rows (inner join on a nullable key) is a bug until shown
   otherwise. Count rows before and after.
4. **Nulls, types, time.** Nulls in keys and in `NOT IN`/`=` comparisons; silent casts that truncate;
   time zones and DST; `timestamp` vs `date`; division by zero; empty input.
5. **Schema change.** What happens when upstream adds, renames or drops a column, or changes a type.
   `SELECT *` into a fixed target is a risk. Is there a contract or test on the input?
6. **Data quality.** Tests on the output: unique and not-null keys, accepted values, row count within a
   range of the last run, freshness. One failing check should stop the publish, not just log.
7. **Cost and speed.** Full scans where a partition or cluster filter would do; a query per row; a
   cross join; recomputing all history each run when incremental would do.
8. **Sensitive data.** PII or customer data copied into logs, samples, dev tables or prompts; access
   wider than the source had.

## Report

For each finding: what the data looks like that breaks it, what wrong output follows, the fix, and a
query or test that shows it. No concrete case, no finding. End with the checks you could not run (for
example, no access to production data) so the person knows what is unproven.
