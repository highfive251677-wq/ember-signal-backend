# Ember Signal Worker Assignments — 2026-09-17

## Command hierarchy

```text
Supervisor — စူပါဗိုက် (Manus)
        ↓ assigns and audits
LED — team leader
        ↓ coordinates
L — မီးအိမ်     D — စစ်တံခါး     E — မျက်စိစောင့်
```

The Supervisor is not LED. The Supervisor assigns bounded work to LED, reviews LED's coordination and the L/D/E outputs, checks connectors and KPIs, and decides whether the team may advance. LED leads the workers on the other side; LED does not self-approve a material decision.

## Supervisor — စူပါဗိုက်

**Owner:** Manus in the current session.

**Responsibilities:** Assign one bounded task to LED; specify acceptance criteria, required L/D/E handoffs, primary connector, mutation boundary, and stop condition; independently inspect the team packet; check Railway, GitHub, local data, connector status, provenance, and KPIs; return `PASS`, `FAIL`, `INCOMPLETE`, or `BLOCKED`; and authorize only the next safe step.

**Must not:** Pretend to be LED, accept LED's summary without evidence, self-approve a publication/merge/deployment, or bypass the E gate.

## LED — team leader

**Task ID:** `dup-002-supervisor-assigned`

**Responsibilities:** Receive the Supervisor's packet; assign distinct bounded tasks to L, D, and E; integrate their report envelopes; run reversible validation; prepare the team checkpoint; and return the complete packet to the Supervisor.

**Must not:** Self-approve, auto-merge, delete, remap foreign keys, publish, deploy, or hide a worker/provider failure.

**Required handoffs:**

- L: public-source research for institutions 116 and 122.
- D: data/provenance/schema audit of the candidate and L packet.
- E: independent review and one release verdict.

## L — မီးအိမ်

**Task ID:** `dup-002-source-research`

Find official, public, accessible sources for institution IDs 116 and 122 that establish identity, address, township, contact, registration/affiliation, or evidence that the records are separate. Record source URL, title, institution match, location, observed date, accessibility, robots/access uncertainty, excerpt, and uncertainty.

Do not use login/private content, bypass controls, guess social ownership, approve a source, write to the database, or make a merge decision. If no authoritative evidence is found, report that clearly.

**Primary connector:** Public web/source access. Mistral may translate or extract fields after source capture; the output remains assistive.

## D — စစ်တံခါး

**Task ID:** `dup-002-data-audit`

Audit the L packet and local candidate 2. Confirm candidate reasons, source/evidence counts, canonical URLs, foreign-key impact, schema integrity, and unchanged institution/source/evidence rows. Return an audit diff and a recommendation such as `NEEDS_HUMAN_EVIDENCE`, `KEEP_SEPARATE_REVIEW`, or `MERGE_REVIEW_ONLY`; never perform the merge.

**Primary connector:** Local repository/database and GitHub read-only review. DeepSeek/OpenAI may provide one report-only technical audit if access is available, without sending the full database.

## E — မျက်စိစောင့်

**Task ID:** `dup-002-independent-gate`

Independently compare L and D outputs with the original sources and project policy. Return exactly one `PASS`, `FAIL`, `INCOMPLETE`, or `BLOCKED`, with cited evidence, unresolved risks, KPI impact, and whether a human decision is permissible.

Candidate 2 currently has no source/evidence records on either side; a high matcher score alone is insufficient. The expected initial outcome is `INCOMPLETE` or `BLOCKED` unless authoritative evidence is added.

**Primary connector:** Gemini structured independent review. If unavailable, record `PROVIDER_BLOCKED`; use at most one declared fallback with the same schema.

## Handoff order

```text
Supervisor assigns LED
  → LED assigns L/D/E
  → L researches
  → D audits L and local data
  → LED integrates and validates
  → E independently gates
  → LED returns packet to Supervisor
  → Supervisor decides the next task
```

A human decision may be recorded as `KEEP_SEPARATE`, `MERGE_APPROVED`, or `NEEDS_REVIEW` only when provenance is sufficient. `MERGE_APPROVED` additionally requires a canonical institution ID and foreign-key impact notes. No merge implementation may run before a separate migration plan and approval.

## Connector and KPI discipline

Use one primary connector per bounded task. Mistral is for translation/extraction, Gemini for E's independent review, Groq for compact report-only classification if access is restored, and DeepSeek/OpenAI for technical audits. OpenRouter is a named fallback only. Record provider, model, status, error class, and `production_changed: false`.

Release remains `INCOMPLETE` while the 25-item evidence queue, 79 pending duplicate candidates, missing human decisions, regression tests, and E's final release review remain open. Source expansion is blocked.
