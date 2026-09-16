# D Audit — Candidate 2

- **Task:** Audit L's public-source packet for institution IDs `116` and `122`
- **Role:** စစ်တံခါး — D
- **Mode:** audit-only
- **Date:** 2026-09-17

## Audit verdict

**INCOMPLETE — no merge or data mutation authorized.**

## Findings

### 1. Candidate match reason

The local institution rows match exactly on normalized name, city, township, and type:

- Name: `UNIVERSE Vocational School (Centre)`
- City: `Yangon`
- Township: `ကမာရွတ်မြို့နယ်`
- Type: `Private Higher Education Centre`

L found two secondary public directory listings that independently repeat the same apparent Kamayut/Hledan address and phone numbers. This supports a duplicate hypothesis but does not establish canonical ownership or a merge authority.

### 2. Source and evidence counts

| Institution ID | Source rows | Evidence rows |
|---:|---:|---:|
| 116 | 0 | 0 |
| 122 | 0 | 0 |

Both rows therefore have no source/evidence foreign keys to remap.

### 3. URL and canonicalization

No URL exists in `institution_sources` for either institution. The public directory URLs are research references only and were not inserted into the source table. No canonicalization or verification mutation occurred.

### 4. Foreign-key impact

Current direct impact is zero: no `institution_sources` or `evidence_items` rows reference IDs `116` or `122`. However, a future merge would still alter the institution denominator and could affect downstream exports, coverage matrices, correction requests, or external consumers. No remapping is authorized.

### 5. Before/after database counts

No data mutation was performed. Before and after counts are identical for this task:

- `institutions`: 357
- sources for IDs 116/122: 0
- evidence for IDs 116/122: 0
- duplicate decisions: 0

### 6. Schema integrity

The expected core tables exist, including `institutions`, `institution_sources`, `evidence_items`, and `correction_requests`. The local database currently has no populated `duplicate_candidates` or `duplicate_decisions` rows, despite the repository's report-only duplicate workflow and the organizer's separate queue count. This is a material state discrepancy that must be reconciled before any candidate decision is recorded.

### 7. Queue discrepancy

The organizer reported 79 duplicate candidates and 79 pending candidates. The checked local `ember_signal.db` reports:

```json
{"institutions":357,"duplicate_candidates":0,"pending_candidates":0,"decisions":0}
```

This is **not** evidence that the 79 candidates are resolved. It indicates that the candidate queue is not present in this database snapshot or exists in another data artifact/runtime. D recommends locating the authoritative queue before recording candidate 2's decision.

## D recommendation

- Preserve IDs 116 and 122 unchanged.
- Do not add secondary directory listings as verified sources.
- Do not create evidence items from search snippets or login-gated Facebook pages.
- Mark Candidate 2 as `INCOMPLETE`, not `MERGE_APPROVED`.
- Reconcile the authoritative 79-candidate queue with the local database before continuing adjudication.
