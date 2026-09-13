# Task Queue

## P0 — Duplicate institution review (current task)
Inspect the database and code. Produce a report listing the 28 duplicate groups, the proposed canonical institution for each group, and any source/evidence foreign-key impact. Do not merge or delete records yet. Run only this task in the current execution and pause after the report is complete.

## P0 — Evidence review design
Inspect the evidence schema and dashboard. Propose a safe review workflow for the 41 unreviewed evidence records. Do not mark evidence approved without explicit review criteria.

## P1 — Source quality audit
Verify that source registration, verification status, URL canonicalization, robots.txt checks, and collector filtering cannot admit unverified or restricted sources.

## P1 — Tests
Add or improve tests for verified-only collection, robots failure closed, minimum delay enforcement, duplicate detection, and evidence review status.

## P2 — Independent release review
After P0/P1 work is reviewed and tested, return exactly one of: PASS, FAIL, BLOCKED, with evidence and remaining risks.

## Execution rule
Work on one task at a time. Start with analysis/report-only work. Do not deploy or add new collection sources until the independent release gate is PASS. In conservative mode, do not start the next queue item automatically; wait for explicit organizer instruction.
