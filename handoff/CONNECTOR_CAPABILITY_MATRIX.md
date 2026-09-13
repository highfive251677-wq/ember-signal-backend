# Connector Capability and Task Assignment Matrix

## Operating rule
Each connector receives only the task it is best suited for. One task uses one primary provider. A second provider is used only for a material cross-review or an explicit fallback. Every task is report-only unless the organizer separately approves an implementation step.

| Connector | Best capability | Assigned Ember Signal task | Smallest useful input | Output | Not responsible for |
|---|---|---|---|---|---|
| DeepSeek API | Technical reasoning and code/database audit | Analyze one duplicate-institution group batch and propose safe canonicalization queries | Schema plus one bounded duplicate batch | Findings, SQL/query plan, risks, acceptance checks | Final release approval or data mutation |
| Gemini API | Structured classification and JSON extraction | Classify one evidence batch against the approved review schema | Evidence title, excerpt, source status, institution ID | Strict JSON dispositions with notes | Deploying or approving its own output |
| OpenAI API | Independent reasoning and final cross-check | Review one completed audit report for contradictions and release risks | Primary report plus cited evidence only | PASS/FAIL/BLOCKED with reasons | Editing production or replacing evidence |
| Groq API | Fast short-text classification | Tag one small set of new public-source excerpts | Short excerpts and allowed labels | Compact labels and confidence | Long research or final decisions |
| Mistral API | Translation and multilingual extraction | Translate or extract fields from one Burmese/English evidence batch | Only the selected text and target schema | Structured translated/extracted fields | Source verification or release approval |
| OpenRouter API | Controlled model gateway and fallback | Retry one failed primary task with an explicitly selected model | Same bounded input as failed task | Same report envelope plus fallback metadata | Being called in parallel with the primary |

## Capability tests

Capability tests are real but bounded work items, not generic model questions:

1. DeepSeek: produce a duplicate-review plan for one bounded group batch.
2. Gemini: classify five evidence records into the approved schema.
3. OpenAI: cross-check one DeepSeek report and return a release risk verdict.
4. Groq: tag ten short excerpts with the allowed signal labels.
5. Mistral: translate/extract five selected multilingual excerpts.
6. OpenRouter: remain idle unless one primary test fails; then run exactly that failed test with a named model.

## Success criteria

A connector passes only when it returns the required schema, stays within scope, cites the supplied evidence, and does not claim unauthorized access or changes. A model's own answer does not prove capability; the supervisor validates format, coverage, and policy compliance.

## Current conservative execution

Only one capability test may run in one execution. The current queue remains the P0 duplicate-review task. After one test or terminal provider error, save the report and pause. Do not automatically run the other five tests.
