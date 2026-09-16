# Ember Signal Master Route — 2026-09-16

## Executive decision

Ember Signal is **operationally healthy but release-quality incomplete**. Railway is healthy, the public API is responding, and the publication rule is correctly restrictive. The next route is quality-first: restore local/live schema parity, regenerate the duplicate candidate queue locally, review candidates one at a time, finish evidence dispositions, audit source controls, add regression tests, and obtain an independent release gate before any source expansion.

A small verified public signal is more valuable than broad unreviewed coverage.

## Verified baseline

### Live Railway

- Service: `ember-signal-backend`
- Public health: `/api/health`, `/api/dashboard`, `/api/signals`, and `/api/methodology` returned HTTP 200.
- Database: `ok`
- Institutions: `357`
- Sources: `113` total in the health response; `59` verified in the dashboard totals.
- Verified/public evidence: `6`
- Quarantined evidence: `6`
- Review queue: `25`
- Source coverage: `6.7%`
- Signal mix: 2 course, 2 admissions, 1 partnership, 1 campaign.
- Latest deployed commit: `5878761` after the connector artifact finalization; the last known Railway deployment was successful after the `RAILWAY_TOKEN` correction.

### Repository

- GitHub issues: none recorded in the queried list.
- Pull requests: none recorded in the queried list.
- Main branch is at commit `5878761`.
- Local working tree contains an uncommitted `ember_signal.db` state and it must not be discarded.

### Integrity finding

The local `ember_signal.db` currently lacks the `duplicate_candidates` and `duplicate_decisions` tables, while `duplicate_workflow.py` creates them on demand and the older checkpoint described a 79-candidate queue. Therefore the local queue state is not currently reproducible from the checked-out database. This is a **schema/state parity finding**, not evidence that production is corrupt. Repair locally first; do not mutate production to make local counts match.

## Four-worker operating model

| Worker | Role | Current assignment | Output | Gate |
|---|---|---|---|---|
| LED | Lead/coordinator/implementer | Define one bounded task, integrate outputs, run validation, checkpoint | Implementation or decision packet | Cannot self-approve |
| မီးအိမ် — L | Public-source researcher | Find official accessible institution sources only for the selected candidate/evidence item | URL, institution match, location, provenance, uncertainty | Cannot verify own source |
| စစ်တံခါး — D | Data/quality auditor | Check schema parity, duplicate queue, provenance, robots rules, tests, and count deltas | Audit diff and test result | Cannot merge/delete |
| မျက်စိစောင့် — E | Independent release reviewer | Recheck the packet against source, policy, and KPI requirements | PASS/FAIL/INCOMPLETE/BLOCKED | Cannot modify production |

For one runtime, run these as separate passes with separate evidence notes. Do not collapse L, D, and E into one unsupported model answer.

## Connector assignments

- Railway API: read-only deployment/log/variable inspection.
- GitHub: issue, PR, commit, and source review.
- Mistral: Burmese/English translation and structured extraction; preserve original text.
- Groq: one-record compact evidence label when completion access is available; current 403 remains `PROVIDER_BLOCKED`.
- Gemini: independent review of one duplicate/evidence packet; do not merge.
- DeepSeek or OpenAI: independent operational/code audit only when access and quota are confirmed.
- OpenRouter: one declared fallback only; never fan out providers for the same item.

## Staged route and gates

### Stage 0 — Restore reproducibility (current)

1. Preserve the local database file.
2. Run the existing duplicate workflow initializer/generator locally; it may create only candidate and decision tables and candidate rows.
3. Verify institution/source/evidence counts are unchanged and confirm candidate count.
4. Record the local queue hash/count and keep production untouched.

**Exit gate:** local schema has the required candidate tables; candidate generation is repeatable; no institution/source/evidence row changed.

### Stage 1 — Candidate adjudication

Process one high-confidence candidate per bounded run.

1. L obtains public official address/contact/registration evidence.
2. Gemini may independently summarize the supplied packet.
3. D checks source identity, foreign-key impact, and duplicate logic.
4. E issues `PASS`, `INCOMPLETE`, or `BLOCKED` for the packet.
5. A human records `KEEP_SEPARATE` or `MERGE_APPROVED` with canonical ID and notes.

No merge implementation is designed until multiple decisions and their impact notes exist. No AI output can become a human decision automatically.

### Stage 2 — Evidence review

Review the live queue of 25 one record at a time. For each item retain source URL, observed time, excerpt, hash, institution match, and review state. Use Mistral only for translation/extraction; use Groq only for a report-only label when access is restored. Human review determines `approved`, `source_review_required`, `rejected`, or `quarantined`.

**Exit gate:** 100% of the current review queue has a disposition, and every published signal has verified source plus human-approved evidence.

### Stage 3 — Source-quality audit

D audits source registration, canonical URLs, verification status, robots failure-closed behavior, verified-only collector filtering, and minimum request delay. L supplies only the missing public-source facts needed for the selected audit sample.

**Exit gate:** restricted/private/robots-disallowed collection remains zero; tests cover each quality control.

### Stage 4 — Regression and release review

Add or run tests for collector filtering, robots denial, delay enforcement, duplicate candidate generation, evidence status transitions, correction history, and approved-only public output. E independently reviews the final packet.

**Release verdict:** exactly one of `PASS`, `FAIL`, `INCOMPLETE`, or `BLOCKED`.

### Stage 5 — Controlled expansion

Only after E returns `PASS`: expand sources in small auditable batches, use low-frequency collection, monitor KPI deltas, and stop on any material provenance or access-control error.

## KPI gates

| KPI | Target | Current verdict |
|---|---:|---|
| Provenance for published signals | 100% | On track; must remain enforced |
| Evidence review disposition | 100% of current queue | **INCOMPLETE**; 25 live queue items |
| Restricted/private/robots-disallowed collection | 0 | Must be re-audited |
| Duplicate groups with disposition | 100% before expansion | **BLOCKED**; no current human decisions |
| Material claims with traceable evidence | 100% | **INCOMPLETE** |
| Schema/regression tests | Pass | **INCOMPLETE**; local parity finding open |
| Independent review | E agrees | **INCOMPLETE** |
| Premature release | 0 | PASS so far; preserve this |

## Do not do yet

- Do not add new collection sources.
- Do not auto-merge duplicates.
- Do not change production database records.
- Do not publish from model output alone.
- Do not create a recurring worker or 24/7 operator before release PASS.
- Do not treat a healthy HTTP 200 as proof of data quality.

## Immediate next task

**LED + D:** regenerate and verify the local duplicate candidate queue without changing institution, source, or evidence rows. Stop after the count/hash checkpoint.
