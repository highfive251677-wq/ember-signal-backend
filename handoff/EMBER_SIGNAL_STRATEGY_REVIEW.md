# Ember Signal Strategy Review

## Executive conclusion

Ember Signal is moving in a potentially useful direction, but it is not yet ready to expand as a broad education-intelligence product. Its strongest current asset is the quality-control foundation: verified-source collection, robots-aware public access, evidence records, and independent review gates. Its largest weakness is that the system is collecting faster than it is converting observations into reviewed, traceable, decision-useful intelligence. The correct near-term strategy is therefore **quality before coverage, public benefit before monetization, and decision products before a large database**.

The project should borrow four practices from comparable brands. From QS, it should adopt explicit indicator definitions, published weights, and methodology change logs. From Coursera, it should measure outcomes rather than activity volume. From HolonIQ, it should turn raw records into decision frameworks for education leaders. From LinkedIn Economic Graph, it should use a consistent baseline, publish update cadence, and build partnerships around public-interest questions. It should not copy rankings, opaque scoring, unverified social signals, or growth claims that cannot be independently reproduced.

## What the comparable brands demonstrate

| Brand | Transferable practice | Limitation for Ember Signal |
|---|---|---|
| QS | Separates lenses, indicators, and metrics; publishes indicator weightings and reviews them periodically.[1] | A single ranking can create false precision and competition. Ember should avoid ranking institutions until data coverage and comparability are defensible. |
| Coursera | Measures learner outcomes such as career outcomes, personal benefit, skills, and access rather than reporting enrollment alone.[2] | Self-reported outcome data can contain selection and response bias. Ember should label evidence type and uncertainty. |
| HolonIQ | Packages data, research, benchmarks, frameworks, and case studies around decisions such as growth, innovation, enrollment, and partnerships.[3] | Its commercial intelligence model is not a direct fit for a public-interest project. Ember should publish a free core layer and keep decision support explainable. |
| LinkedIn Economic Graph | Uses a stable baseline, explicit methodology, recurring updates, large-scale skills/workforce signals, and partnerships with public institutions.[4] | Platform data is not representative of the whole population. Ember must not treat public social activity as a proxy for institutional quality or social impact. |

## What Ember Signal should adopt now

### 1. Publish a data dictionary and methodology

Every institution, source, evidence item, signal type, confidence value, and review status should have a plain-language definition. Each metric should identify its unit, observation window, source type, limitations, and last update. If a score is introduced later, its components and weights must be public, versioned, and reproducible.

### 2. Separate observation from interpretation

The system should distinguish between an observed fact and an interpretation. For example, “a public page mentions an intake” is an observation. “The institution is expanding aggressively” is an interpretation and requires additional evidence. This separation is essential for public trust and prevents marketing language from being mistaken for intelligence.

### 3. Build outcome-oriented public products

The first useful products should answer concrete questions: which institutions publicly announce accessible learning opportunities; which course areas are appearing; what public information is missing; and where learners may need verification or caution. The project should measure usefulness through corrected records, verified signals, user questions answered, and decisions supported—not through institution count alone.

### 4. Introduce a correction and provenance system

Each published signal should retain its source URL, observed time, collector status, review status, reviewer note, and correction history. A public correction mechanism should allow an institution or reader to report an error without giving them unilateral authority to approve their own record.

### 5. Establish a stable update cadence

The project should publish a clear cadence such as weekly collection summaries and monthly methodology/status reports. If a source is unavailable, restricted, stale, or ambiguous, the system should display that limitation rather than silently treating the record as current.

### 6. Use partnerships for public value

Potential partners include education researchers, student groups, libraries, skills organizations, and responsible institutions. Partnership goals should be specific: validating definitions, identifying missing institutions, improving accessibility, or testing whether the outputs help learners. Partnerships must not become a channel for preferential ranking or data suppression.

## What should be stopped or rejected

The project should stop expanding source coverage when the evidence review queue is growing faster than reviewer capacity. It should reject any automatic approval of evidence from unverified sources, private pages, login-gated content, or robots-disallowed pages. It should reject institution rankings until there is sufficient comparable data and a published methodology. It should reject unsupported “market leader,” “best college,” or “high growth” claims. It should reject duplicate expansion that increases the institution count without improving canonical identity quality.

The project should also stop treating connector availability as progress. Having many AI providers is infrastructure, not impact. An AI call that does not improve classification accuracy, traceability, or a decision product is unnecessary cost. Deterministic checks must remain local, and only one assigned model should be called for a bounded task.

## Current Ember Signal diagnosis

The latest known production baseline is 357 institutions, 69 registered sources, 53 verified sources, 57 evidence records, 51 unreviewed evidence records, 28 known duplicate institution groups, and 0 verified evidence in the last health check. The latest collection pass added 16 unreviewed evidence records from verified sources; one source returned HTTP 403 and was correctly skipped. This demonstrates that the collector is functioning, but it also shows that collection is ahead of review. New collection should therefore pause until the review and duplicate queues are reduced.

The project currently has a credible technical safety direction, but it has not yet demonstrated public usefulness at scale. The next milestone should not be “more institutions.” It should be “a small, independently reviewed public insight that a learner, researcher, or education organization can use and verify.”

## Proposed 90-day sequence

| Period | Objective | Exit criteria |
|---|---|---|
| Days 1–30 | Quality reset | Resolve or document all 28 duplicate groups; review the existing evidence queue; publish the data dictionary; retain a full provenance trail. |
| Days 31–60 | Public usefulness test | Release one small public dashboard or report focused on a defined question; recruit a small set of independent users; record corrections, missing data, and usefulness feedback. |
| Days 61–90 | Sustainable operating model | Publish the first methodology/version report; establish update cadence; define one free public product and one optional paid research/service layer without restricting core public facts. |

## KPI framework

| Dimension | KPI | Initial target |
|---|---|---:|
| Data quality | Duplicate groups resolved or dispositioned | 28/28 |
| Evidence quality | Existing evidence reviewed with notes | 100% |
| Provenance | Published signals with source URL and observed time | 100% |
| Public safety | Restricted/robots-disallowed sources collected | 0 |
| Accuracy | Material corrections after publication | Track and reduce monthly |
| Public benefit | Independent users who report a useful decision or discovery | Establish baseline in first 30 days |
| Accessibility | Core public report available without payment or login | 100% of core report |
| Sustainability | Monthly operating cost per verified insight | Track before scaling |
| Discipline | AI requests with clear task owner and bounded output | 100% |

## Decision rule

Ember Signal should expand only when the current quality gates pass and a public-usefulness test shows that the output helps real users. If a serious error appears—fabricated source, privacy breach, systematic duplicate inflation, misleading score, or unauthorized access—the affected pipeline should stop immediately, the records should be quarantined, and the project should publish a correction note before resuming.

The strategic direction is therefore **continue, but narrow the scope**. Keep the verified public-source foundation. Stop broad collection for now. Turn the existing 57 observations into reviewed, explainable, public-benefit intelligence. Then expand only from evidence of accuracy and usefulness.

## References

[1]: https://www.topuniversities.com/world-university-rankings/methodology "QS World University Rankings: Methodology"

[2]: https://www.coursera.org/explore/learner-outcomes "Coursera Learner Outcomes Report"

[3]: https://www.holoniq.com/universities "HolonIQ for Universities"

[4]: https://economicgraph.linkedin.com/ "LinkedIn Economic Graph"
