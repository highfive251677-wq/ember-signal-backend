# Ember Signal Worker Assignments — 2026-09-17

## Operating decision

The four workers operate as a controlled handoff, not an uncontrolled fan-out. Only one bounded task is active at a time. The current task is duplicate candidate 2, covering institution IDs 116 and 122. No worker may merge, delete, publish, deploy, or change production data.

## Worker 1 — LED / စူပါဗိုက်

**Role:** Lead, coordinator, implementer, and release organizer.

**Active responsibility:** Define the Candidate 2 evidence packet, provide the exact acceptance criteria, integrate L/D/E outputs, run local validation, and write the checkpoint.

**Required output:** A complete report envelope with task ID, role, provider, mode, claims, evidence references, risks, mutations, next action, and confidence.

**Must not do:** Self-approve the duplicate, silently bypass E, or deploy/publish before a gate passes.

**Connector use:** Manus/API-level orchestration only if a durable worker task is actually needed; no external task creation is required for this bounded local review. GitHub and Railway remain read-only during this stage.

## Worker 2 — မီးအိမ် / L

**Role:** Public-source researcher.

**Task ID:** `dup-002-source-research`

**Scope:** Research only institution IDs 116 and 122. Find official, public, accessible sources that can establish identity, address, township, contact details, registration/affiliation, or evidence that they are separate entities. Search results alone are not proof.

**Required output:** For each URL, record source URL, page title, institution match, city/township, observed date, accessibility, robots/access uncertainty, relevant excerpt, and confidence. State clearly when no authoritative evidence is found.

**Forbidden:** Login/private content, access-control bypass, robots-disallowed collection, guessed social ownership, source verification approval, database writes, and merge decisions.

**Primary connector:** Public web/source access. Mistral may translate or extract fields only after the source is captured; its output remains assistive.

**Stop condition:** Stop if the source is inaccessible, ambiguous, private, or cannot be tied to one of the two records.

## Worker 3 — စစ်တံခါး / D

**Role:** Data and quality auditor.

**Task ID:** `dup-002-data-audit`

**Scope:** Audit the L packet and local candidate 2. Confirm the candidate reason, source/evidence counts, canonical URL treatment, foreign-key impact, schema integrity, and that no institution/source/evidence rows changed.

**Required output:** An audit diff containing before/after counts, candidate metadata, missing evidence, risks, and a recommendation of `NEEDS_HUMAN_EVIDENCE`, `KEEP_SEPARATE_REVIEW`, or `MERGE_REVIEW_ONLY`—never a merge action.

**Forbidden:** Deleting, merging, remapping foreign keys, marking a source verified, approving evidence, or modifying production.

**Primary connector:** Local repository/database inspection and GitHub source review. Use DeepSeek/OpenAI only for an independent report-only code audit if access is available; do not send the full database.

**Stop condition:** Stop for schema drift, unexplained count changes, missing provenance, or foreign-key ambiguity.

## Worker 4 — မျက်စိစောင့် / E

**Role:** Independent reviewer and release gatekeeper.

**Task ID:** `dup-002-independent-gate`

**Scope:** Review the completed L and D packet independently. Compare each claim to the original source and project policy. Decide exactly one of `PASS`, `FAIL`, `INCOMPLETE`, or `BLOCKED` for the review packet.

**Required output:** Independent verdict, cited evidence, unresolved risks, KPI impact, and whether a human decision is now permissible. A high matcher score alone is insufficient; Candidate 2 currently has no source/evidence records, so the default is expected to remain `INCOMPLETE` or `BLOCKED` unless new authoritative evidence is found.

**Forbidden:** Editing code/data, changing review status, approving own work, merging, publishing, or deploying.

**Primary connector:** Gemini for structured independent review. If Gemini is unavailable, record `PROVIDER_BLOCKED`; use at most one predeclared fallback and preserve the same schema.

**Stop condition:** Stop if evidence is missing, source access is uncertain, provenance is incomplete, or L/D disagree materially.

## Handoff order

```text
LED defines packet
  → L researches public evidence
  → D audits data and provenance
  → LED validates and assembles
  → E issues independent gate
  → human records decision if and only if evidence is sufficient
```

The human decision vocabulary is `KEEP_SEPARATE`, `MERGE_APPROVED`, or `NEEDS_REVIEW`. `MERGE_APPROVED` additionally requires an explicit canonical institution ID and foreign-key impact notes. No implementation may apply the merge until the human decision is recorded and a separate migration plan is reviewed.

## Connector and token discipline

Use one primary connector per task. Do not send the same candidate to every provider. Mistral is for translation/extraction, Gemini for independent review, Groq for compact evidence labels only if access is restored, and DeepSeek/OpenAI for technical audits. OpenRouter is a named fallback, not a parallel route. Record provider, model, status, usage when available, and `production_changed: false`.

## KPI gate for this assignment

The assignment can close only when provenance for every claim is complete, no restricted/private source was used, local counts are unchanged, no production mutation occurred, and E has issued a verdict. This assignment does not by itself clear the project release gate; all duplicate dispositions, evidence review, tests, and independent release review remain required.

## Current status

- LED: active.
- L: pending Candidate 2 public-source packet.
- D: waiting for L packet; local queue is reproducible with 79 pending candidates.
- E: waiting for L and D outputs.
- Project release: `INCOMPLETE`; source expansion remains blocked.
