# Connector Run Status — 2026-09-16

## Groq

The repository-side Groq classifier is finalized as a report-only, one-record prototype in `classify_evidence_groq.py`. It selects exactly one record whose source is verified and whose evidence review status is unreviewed. It returns a bounded JSON recommendation with `signal_type`, `suggested_review_status`, `reason`, and `confidence`. It never changes `review_status`, merges institutions, remaps foreign keys, or writes production data.

The live completion test returned HTTP 403. The Groq model-list endpoint was reachable, but the completion request was not authorized for the selected model/account. The result is therefore recorded as `PROVIDER_BLOCKED`, not as a classification. The runner must not retry repeatedly or treat the failure as an approval.

## Mistral

The repository-side Mistral demo is finalized in `mistral_api_demo.py`. It supports one mode per invocation: model discovery, chat, structured JSON extraction, and translation. Model discovery succeeded on 2026-09-16, and the non-secret snapshot is stored in `MISTRAL_MODELS_SNAPSHOT_2026-09-16.json`.

A bounded translation test returned HTTP 429 `Rate limit exceeded`. This is recorded as `PROVIDER_RATE_LIMITED`, not as a failed translation and not as a reason to retry immediately. When access is available, Mistral's preferred role is multilingual extraction and translation of already collected public evidence. It must not decide source verification or approve publication.

## Final routing

| Task | Primary connector | Output | Approval rule |
|---|---|---|---|
| Short evidence label | Groq | Compact classification JSON | Human review required |
| Myanmar/English translation | Mistral | Translation only | Compare to source text |
| Structured multilingual field extraction | Mistral | Schema-validated JSON | Evidence provenance required |
| Duplicate adjudication | Human reviewer; Gemini as report-only assistant when available | Keep-separate or merge recommendation | Human decision required |
| Final release cross-check | OpenAI/DeepSeek when balance is available | Audit report | Never self-approve |

## Current safe state

- No Groq classification was finalized as an evidence decision.
- No Mistral translation was published.
- No database status changed.
- No duplicate was merged.
- No production deployment was changed.
- Provider errors are preserved as operational status, not hidden.
