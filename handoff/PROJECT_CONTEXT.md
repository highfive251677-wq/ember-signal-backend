# Ember Signal — Project Handoff Context

## Purpose
Ember Signal is a public-source intelligence system for Myanmar colleges and education institutions. It records institutions, verified public source URLs, public activity signals, and evidence with a quality-review trail.

## Production
- Service: https://ember-signal-backend-production.up.railway.app
- Health: https://ember-signal-backend-production.up.railway.app/api/health
- Dashboard data: https://ember-signal-backend-production.up.railway.app/api/dashboard
- Previous known commit: `f7b70ed`

## Current known status
- Database: OK
- Institutions: 357
- Sources: 69
- Evidence: 41
- Source coverage: 7.3%
- Unreviewed evidence: 41
- Known duplicate institution groups: 28

## Roles
- Source Researcher: finds official public sources only.
- Quality Auditor: checks duplicates, verification, robots.txt, URL canonicalization, evidence quality, and local/live counts.
- Independent Reviewer: does not modify code; returns PASS, FAIL, or BLOCKED.
- Implementer: writes code, runs tests, commits, and deploys only after review.

## Non-negotiable rules
1. Use only public, accessible sources.
2. Prefer verified official websites and official public social accounts.
3. Never access private or login-gated content.
4. Never bypass robots.txt or access restrictions.
5. Do not automatically collect from unverified sources.
6. Keep at least 0.5 seconds between collector requests.
7. Do not add a new source batch until quality review is complete.
8. Do not deploy until the independent review is PASS.
9. Check for duplicate institutions before inserting data.
10. Preserve an audit trail for every data change.
11. Never make destructive database changes without backup and explicit review.
12. Never expose API keys in source files, logs, commits, or prompts.

## Handoff protocol
A new worker must first inspect this file, `CURRENT_STATUS.md`, `TASK_QUEUE.md`, and the repository. It must report what it understands before modifying code. It must not claim completion without running relevant tests and checking the live API where applicable.

## DeepSeek role
DeepSeek is an assisting worker for inspection, analysis, tests, and draft changes. It is not the final release authority. All changes require local review, tests, and the independent PASS gate before deployment.

## First priority
Resolve the 28 duplicate institution groups and review the 41 evidence records. Do not expand collection coverage until those quality issues are addressed.
