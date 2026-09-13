# Token Budget and Task Discipline

## Objective
Use provider tokens only when they add distinct value. Every request must have one owner, one bounded objective, a compact context, and a bounded response. Ember Signal runs in conservative mode: one task at a time, one provider at a time, and a pause after the current task when ten percent of the configured daily budget has been consumed.

## One-task ownership

| Task | One primary provider | Maximum output | Fallback |
|---|---|---:|---|
| Technical/code/database audit | DeepSeek | 1,200 tokens | OpenRouter only after a provider error |
| Evidence classification/schema | Gemini | 800 tokens | OpenRouter only after a provider error |
| Final release review | OpenAI | 700 tokens | OpenRouter only after a provider error |
| Short-text classification | Groq | 300 tokens | No automatic fallback for a single short item |
| Translation/extraction | Mistral | 600 tokens | OpenRouter only for a failed batch |

## Conservative execution mode

1. Work on exactly one queue item per run, in priority order.
2. Use exactly one primary provider per queue item.
3. Use a fallback only when the primary returns a provider error and the task explicitly permits fallback. The fallback counts as the same task, not a new parallel task.
4. After the current task reaches a complete report or a terminal error, stop and pause. Do not start the next queue item automatically.
5. If estimated usage reaches ten percent of the configured daily request or output-token budget, finish only the current request, save its report, and stop with `BUDGET_PAUSED`.
6. Resume only on an explicit organizer instruction after reviewing the saved report and remaining budget.
7. Never use AI for deterministic checks such as counts, exact-URL duplicates, JSON validation, or HTTP health.

## Request rules

1. Send only the relevant record, excerpt, diff, or file section. Never send the full repository when a small excerpt is enough.
2. Reuse the handoff context summary; do not resend the same context repeatedly in a loop.
3. Use one primary request per task. Do not call all providers for ordinary work.
4. Require concise structured output. Prefer JSON or a fixed report template over prose.
5. Set a provider-specific maximum output token value. Never leave output limits unlimited.
6. Retry at most once, and only for a transient network or 5xx error. Do not retry 401, 402, 403, or 429 automatically.
7. Use OpenRouter only as an explicit fallback with a named model. Never call direct and OpenRouter in parallel.
8. Stop the task when the required fields are complete. Do not ask a second model to restate the same answer.
9. Save one request/response audit record containing provider, model, task_id, status, and approximate token usage when the provider reports it. Never save the API key.

## Daily safety limits

The worker must stop and report `BUDGET_BLOCKED` when a configured request or token budget is reached. Conservative mode pauses at ten percent of the configured daily request or output-token budget. These are guardrails and do not guarantee provider billing behavior.

## Approval gates

- Report-only analysis can run with one primary provider.
- Cross-review is required only for material release decisions, not for every routine classification.
- A release decision must use a separate reviewer and the smallest relevant evidence bundle.
- No model can approve its own code, database change, or deployment.

## Practical workflow

```text
Local deterministic check
  → one assigned AI worker
  → complete one report
  → schema/KPI validation
  → pause and save state
  → cross-review only on explicit instruction
  → human/organizer release decision
```
