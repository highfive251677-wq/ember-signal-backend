# Multi-Model Supervision KPIs

## Purpose
Measure whether each AI worker is doing its assigned job accurately, safely, and on scope. A provider's own answer is never accepted as proof of its own quality.

## KPI table

| KPI | Target | Measurement | Gate |
|---|---:|---|---|
| Task completion | 100% of required fields | Compare report to task template | Missing required fields = FAIL |
| Scope adherence | 100% | Confirm no code/data/deploy action in report-only tasks | Any unauthorized action = BLOCK |
| Evidence traceability | 100% of claims | Every material claim cites file, record, URL, or endpoint | Unsupported material claim = FAIL |
| Public-source compliance | 100% | No private/login-gated or robots-disallowed source | Any violation = BLOCK |
| Duplicate review coverage | 28/28 groups | Count groups with recommendation and impact analysis | Fewer than 28 = INCOMPLETE |
| Evidence review coverage | 41/41 records | Count records with explicit disposition and notes | Fewer than 41 = INCOMPLETE |
| Schema validity | 100% | Validate returned JSON against the approved schema | Invalid JSON/schema = FAIL |
| Cross-review agreement | At least 2 independent reviewers agree | Compare independent outputs on material decisions | Disagreement = human review |
| Release decision quality | 0 premature releases | Verify PASS has all checklist evidence | Premature PASS = BLOCK |
| Provider reliability | HTTP 2xx and valid response | Record status/model/error category | 401/402/429/5xx is reported, not hidden |
| Cost control | One primary request per task | Inspect provider routing log | Direct + fallback duplicate = FAIL |

## Required report envelope

Every worker report must include:

```json
{
  "task_id": "...",
  "provider": "...",
  "model": "...",
  "mode": "report-only",
  "status": "PASS|FAIL|INCOMPLETE|BLOCKED",
  "claims": [{"claim": "...", "evidence": "file/url/record"}],
  "findings": [],
  "risks": [],
  "next_actions": [],
  "confidence": 0.0
}
```

## Supervision process

First, the assigned primary model produces a report. Next, a different model checks completeness, evidence links, and policy compliance. If the task affects release, the independent reviewer must issue the final gate. The organizer accepts only the intersection of verified facts; unresolved disagreement remains BLOCKED.

## Release gates

- **PASS:** all KPIs meet target, evidence is traceable, no policy breach exists, and an independent reviewer agrees.
- **FAIL:** a material requirement is contradicted or a safety rule is breached.
- **INCOMPLETE:** work is safe but required coverage is missing.
- **BLOCKED:** a credential, balance, source-access, data-integrity, or approval problem prevents a trustworthy decision.

## Current baseline

The known baseline is 357 institutions, 69 sources, 41 evidence records, 7.3% source coverage, and 41 unreviewed evidence records. New source expansion remains BLOCKED until duplicate and evidence review coverage reaches target and the independent release review is PASS.
