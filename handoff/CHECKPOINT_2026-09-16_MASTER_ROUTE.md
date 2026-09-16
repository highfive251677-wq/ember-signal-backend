# Checkpoint — Master Route — 2026-09-16

## Bounded task completed

Restored the local duplicate workflow schema and regenerated the candidate queue using `duplicate_workflow.py generate`.

## Verified local facts

- Institutions: `357` before and after.
- Sources: `113` before and after.
- Evidence: `41` before and after.
- Duplicate candidates: `79`.
- Pending candidates: `79`.
- Human duplicate decisions: `0`.
- Candidate queue SHA-256 over ordered identity/score/class/status rows: `3d3a2c794d2f3c9eff180460e92f445382fe38047ac43b156602014fd9e1f200`.
- Candidate generation printed: `no institution was changed`.
- Backup: `/tmp/ember_signal_before_queue_repair_2026-09-16.db`.

## Verified live facts

- Railway public endpoints returned HTTP 200.
- Live dashboard totals: 357 institutions, 59 verified sources, 6 evidence records, 6 quarantined, 25 review-queue items, 6.7% source coverage.
- Live public signals remain limited to human-approved verified-source evidence.

## Gate verdict

**INCOMPLETE**. Operational health is PASS, but release quality is not ready. The local queue is reproducible again; no human duplicate decisions, full evidence disposition, independent release PASS, or regression-test completion exists yet.

## Mutations

- Local-only creation of `duplicate_candidates` and `duplicate_decisions` tables.
- Local-only creation of 79 pending candidate rows.
- No institution, source, or evidence row changed.
- No production database, deployment, public signal, credential, or GitHub issue changed.

## Next bounded task

Review candidate `2` (institution IDs `116` and `122`) with L/D/E evidence passes. It is a high-confidence name/location/type match but currently has zero source records and zero evidence records on both sides, so the correct initial state is `NEEDS_HUMAN_EVIDENCE`, not merge.
