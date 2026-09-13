# Token Budget and Task Discipline

## Objective
Use provider tokens only when they add distinct value. Every request must have one owner, one bounded objective, a compact context, and a bounded response.

## One-task ownership

| Task | One primary provider | Maximum output | Fallback |
|---|---|---:|---|
| Technical/code/database audit | DeepSeek | 1,200 tokens | OpenRouter only after a provider error |
| Evidence classification/schema | Gemini | 800 tokens | OpenRouter only after a provider error |
| Final release review | OpenAI | 700 tokens | OpenRouter only after a provider error |
| Short-text classification | Groq | 300 tokens | No automatic fallback for a single short item |
| Translation/extraction | Mistral | 600 tokens | OpenRouter only for a failed batch |

## Request rules

1. Send only the relevant record, excerpt, diff, or file section. Never send the full repository when a small excerpt is enough.
2. Reuse the handoff context summary; do not resend the same context repeatedly in a loop.
3. Use one primary request per task. Do not call all providers for ordinary work.
4. Use a deterministic rule or local code first for simple checks such as counts, duplicates by exact URL, JSON validation, and HTTP health.
5. Require concise structured output. Prefer JSON or a fixed report template over prose.
6. Set a provider-specific maximum output token value. Never leave output limits unlimited.
7. Retry at most once, and only for a transient network or 5xx error. Do not retry 401, 402, 403, or 429 automatically.
8. Use OpenRouter only as an explicit fallback with a named model. Never call direct and OpenRouter in parallel.
9. Stop the task when the required fields are complete. Do not ask a second model to restate the same answer.
10. Save one request/response audit record containing provider, model, task_id, status, and approximate token usage when the provider reports it. Never save the API key.

## Daily safety limits

The worker must stop and report `BUDGET_BLOCKED` when a configured request or token budget is reached. Suggested initial limits are 20 requests per provider per day and 100,000 output tokens per provider per day. These are guardrails, not promises about provider billing.

## Approval gates

- Report-only analysis can run with one primary provider.
- Cross-review is required only for material release decisions, not for every routine classification.
- A release decision must use a separate reviewer and the smallest relevant evidence bundle.
- No model can approve its own code, database change, or deployment.

## Practical workflow

```text
Local deterministic check
  → one assigned AI worker
  → schema/KPI validation
  → cross-review only if material
  → human/organizer release decision
```
