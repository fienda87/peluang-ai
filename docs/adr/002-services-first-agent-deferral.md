# ADR-002: Services-first execution for Recommendation/Feedback/Recovery/Discovery agents

- **Status:** Accepted
- **Date:** 2026-08-23
- **Relates to:** Tech Spec v1.1 §24 (OpenCode Implementation Rules), Service & Module Contract v1.1 §25 (Definition of Done), ADR-001

## Context

Tech Spec v1.1 §24 mandates: "Implement each [agent] as a bounded LangGraph workflow." During Fase B-Revised audit we found all five agent graphs exist, but only **Extraction** is actually invoked in the live pipeline. Recommendation, Feedback, Recovery and Discovery tasks call deterministic services directly, bypassing their graphs.

Wiring all four graphs simultaneously would delay the delivery of real scraped data (the product's most critical gap) without changing user-visible behavior: the underlying services implement identical logic today.

## Decision

1. **Extraction Agent is wired into the pipeline now** (`extract_document_task` → `extraction_graph`). It enforces the fast-path ladder from Runtime Architecture doc §3–4: deterministic first (≥0.5 confidence = 0 LLM calls), LLM fallback within budget (2 calls / 8 steps), Vision for low-confidence images.

2. **Recommendation, Feedback, Recovery, Discovery remain services-first** until their next milestone integration. Their LangGraph graphs stay in `app/agents/` as the canonical state machines; wiring them is tracked work, not a cancellation.

3. This deferral is temporary and must not become permanent. Wiring the remaining four agents requires no new ADR (it is conformance, not change).

## Consequences

- Real data flows end-to-end immediately; agent budget/audit observability is active for extraction runs via `agent_runs`.
- `agent_runs` rows for recommendation/feedback are absent until wiring completes — analytics dashboards will under-report those agent types meanwhile.
- Definition of Done items "All five agents implemented as separate bounded workflows" remains partially unmet (graphs exist, four not routed). Accepted risk, documented here per Contract §26 Change Control.
