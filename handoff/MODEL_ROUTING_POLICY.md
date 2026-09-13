# Model Routing Policy

## Principle
Use direct provider connectors first when the task has a clear primary provider. Use OpenRouter only as a controlled fallback or for an explicitly selected alternate model. Do not send the same request to direct and OpenRouter simultaneously unless a comparison is intentionally requested.

## Primary assignments

| Task | Primary provider | Fallback | Reason |
|---|---|---|---|
| Technical audit, code/database reasoning | DeepSeek API | OpenRouter | Prefer direct DeepSeek for predictable routing and direct provider accounting. |
| Evidence classification and JSON schema | Gemini API | OpenRouter | Gemini is the current primary for structured classification. |
| Final cross-check and release review | OpenAI API | OpenRouter | Prefer direct OpenAI for final independent review when quota is available. |
| Fast short-text classification | Groq API | OpenRouter | Groq is optimized for quick inference. |
| Translation and multilingual extraction | Mistral API | OpenRouter | Mistral is the primary multilingual extraction worker. |

## OpenRouter policy
OpenRouter is a gateway, not a second copy of every direct provider. Use it only when:

1. The primary provider is unavailable, out of quota, or returns a transient error.
2. The task explicitly asks for a different model for comparison.
3. A selected open model is only available through the gateway.

The fallback request must explicitly name a model. Never assume that a provider or model is available. Check the OpenRouter model list before changing the configured model.

## Fallback order

1. Try the assigned direct provider once.
2. Retry the same direct request only for a transient network/5xx error, with a bounded retry count.
3. If the direct provider returns quota/balance/auth failure, stop direct retries.
4. Use OpenRouter only if the task allows fallback and a specific model is configured.
5. Record provider, model, status, and error category in the report.

## Cost and safety rules

- Do not call direct and OpenRouter in parallel for ordinary tasks.
- Do not automatically fall back from an API key/authentication error without recording it.
- Do not let an AI provider write to production, modify the database, or deploy.
- Keep the report-only and human/independent-review gates.
- Keep API keys in secure connector storage only; never place them in code or GitHub.

## Current project workflow

```text
Research/source collection → Mistral or Groq
Evidence classification     → Gemini
Technical/data audit        → DeepSeek
Independent release review → OpenAI
Provider fallback           → OpenRouter, explicit model only
Final decision              → Manus + human organizer
```
