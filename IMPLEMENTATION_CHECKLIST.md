# Peluang.ai — M1-8 to M6 Implementation Checklist

**Status:** M0 + M1-1 to M1-7 complete (committed). Remaining: 59 tasks across M1-8 → M6.

---

## M1 — Multimodal Opportunity Pipeline (remaining 9 tasks)

### M1-8: LLM Extraction Service
- [ ] Create `app/modules/extraction/llm_service.py`
  - Batch extraction (max 3 items/call)
  - Structured output schema (title, description, end_date, organizer, location, prize, category)
  - Prompt engineering: deterministic + semantic fields
  - Fallback to Ollama if OpenRouter fails
- [ ] Test: fixture HTML → extraction result with confidence

### M1-9: Vision-LLM Fallback
- [ ] Create `app/modules/extraction/vision_service.py`
  - Only call if OCR confidence < 0.6
  - Input: image bytes or low-confidence OCR text
  - Output: structured opportunity data
- [ ] Update extraction strategy ladder in agent

### M1-10: Validation Service
- [ ] Create `app/modules/extraction/validation.py`
  - Pydantic schema: title, description, end_date, organizer, location, prize, category, url
  - Date sanity checks (end_date > today, < 5 years future)
  - Required fields enforcement
  - Confidence threshold (≥0.5 → valid, <0.5 → needs_recovery)
- [ ] Mark extraction_results status: valid/invalid/needs_recovery

### M1-11: Deduplication
- [ ] Create `app/modules/deduplication/service.py`
  - Method 1: checksum (raw_documents.checksum already unique)
  - Method 2: URL canonical + normalize
  - Method 3: title fuzzy + date match (pg_trgm similarity > 0.8)
  - Method 4: embedding cosine > 0.95 (after embedding)
  - Resolution: write `dedup_decisions`, link duplicates
- [ ] Test: 3 versions of same opportunity → deduplicated

### M1-12: Opportunity Upsert
- [ ] Create `app/modules/opportunities/service.py`
  - `upsert_opportunity(slug, category, title, ...)`
  - Slug generation: slugify(title + organizer + end_date)
  - Status lifecycle: draft → active (explicit set)
  - Create `opportunity_requirements` from structured data
- [ ] Link raw_document → opportunity

### M1-13: Embedding Batch
- [ ] Create `app/modules/embedding/service.py`
  - Batch embed opportunities (max 100/call)
  - Embed user profiles (async, background)
  - Store in `opportunities.embedding` + `user_profiles.embedding`
  - Reuse cached embeddings (checksum-based)
- [ ] Test: 50 opportunities + 5 users → embedded < 5s

### M1-14: arq Tasks Implementation
- [ ] Update `app/workers/tasks.py`
  - `crawl_source_task(source_id)`: HTML fetcher → store raw docs
  - `extract_document_task(raw_document_id)`: deterministic + LLM + validation
  - `recover_extraction_task(extraction_result_id)`: vision fallback + retry
  - `deduplicate_opportunity_task(opportunity_id)`: call dedup service
  - `generate_recommendation_task(user_id=None)`: M3 (stub for now)
  - `feedback_agent_task(user_id=None)`: M4 (stub)
  - `dispatch_notifications_task()`: M4 (stub)
  - All tasks: error handling, logging, metrics to agent_runs

### M1-15: Extraction Agent (LangGraph)
- [ ] Create `app/agents/extraction/graph.py`
  - State: `raw_document_id`, `strategy`, `extracted_data`, `step_count`, `llm_calls`, `error`
  - Nodes: LOAD → DETECT_TYPE → CHOOSE_STRATEGY → EXTRACT → VALIDATE → (SAVE | RECOVERY)
  - Budget: 8 steps, 2 LLM calls, 60s runtime
  - Strategies: deterministic → LLM → Vision → FAILED
  - Save extraction_results with agent_run_id
- [ ] Test: state transitions + budget enforcement + permission matrix

### M1-16: Fixture Corpus
- [ ] Create `backend/tests/fixtures/`
  - 10 HTML files (various opportunity types)
  - 10 PDF files (text layer + scan mixed)
  - 10 image/poster files (clear + low-quality mixed)
  - Expected extraction output (ground truth)
- [ ] Extraction success ≥90% corpus
- [ ] Duplicate rate ≤5% curated set

**M1 Exit Criteria:**
- 100 opportunities end-to-end pipeline < 90s concurrent
- Extraction success ≥90% fixture
- Duplicate rate ≤5%
- LLM calls/opportunity ≤2 average
- All arq tasks working + agent audited

---

## M2 — User & Matching (11 tasks)

### M2-1: Auth: JWT Local
- [ ] Endpoints: POST `/auth/register`, `/auth/login`, `/auth/refresh`
- [ ] JWT: access (60min) + refresh (30 days)
- [ ] Bcrypt password hashing

### M2-2: Auth: Telegram Link
- [ ] Telegram deep link: `/start?token=JWT`
- [ ] aiogram webhook: `/telegram/webhook`
- [ ] Link `telegram_id` → `user_id` on first bot `/start`

### M2-3: Identity Module
- [ ] `get_profile(user_id)`, `update_profile(user_id, **kwargs)`, `get_preferences(user_id)`
- [ ] Endpoints: GET/PUT `/profile`

### M2-4: Onboarding API
- [ ] POST `/onboarding`: education, major, GPA, skills, interests, goals
- [ ] Store in `user_profiles`

### M2-5: Eligibility Engine (Deterministic)
- [ ] `evaluate_eligibility(user_id, opportunity_id)` → ELIGIBLE | INELIGIBLE | UNKNOWN
- [ ] Rules: GPA exact, education_level exact, major fuzzy (embedding), location optional
- [ ] Write `opportunity_eligibility` table

### M2-6: Eligibility (LLM-Assisted)
- [ ] Semantic requirement interpretation (non-deterministic fields)
- [ ] Confidence + evidence scoring
- [ ] Call AI port with requirement context

### M2-7: Match Features
- [ ] `build_match_features(user_id, opportunity_id)` → feature vector
- [ ] Category fit, location, deadline urgency, semantic similarity (pgvector cosine)

### M2-8: Deterministic Scoring
- [ ] `score_match(user_id, opportunity_id)` → weighted score
- [ ] Weights from `user_preferences.category_weights` (default equal)

### M2-9: Candidate Pipeline
- [ ] `list_candidates(user_id, limit=100)` → open opportunities
- [ ] Filter: explicit constraints → eligibility → soft compat → semantic → top-N
- [ ] Query: <500ms for 300 opportunities

### M2-10: Opportunity Lifecycle Cron
- [ ] Daily arq job: `end_date < today` → status `expired`
- [ ] Re-crawl diff detection → update not duplicate

### M2-11: Search & Filter API
- [ ] GET `/opportunities?q=beasiswa&category=beasiswa&location=jakarta&date_after=2026-09-01`
- [ ] Postgres FTS (`pg_trgm`) + filter
- [ ] Return paginated with eligibility status

**M2 Exit Criteria:**
- User register → onboarding → eligibility evaluated
- INELIGIBLE explicit ≠ candidates
- UNKNOWN ∈ candidates with penalty
- Matching pipeline <500ms for 300 opps

---

## M3 — Recommendation & Action (16 tasks)

### M3-1 to M3-5: Recommendation Agent + Explanation Generator
- [ ] LangGraph: USER_CONTEXT → CANDIDATES → MATCHING → RANK → CONTEXTUAL_REORDER → EXPLAIN → PERSIST
- [ ] Budget: 6 steps, 2 LLM calls, 15s
- [ ] Cannot override INELIGIBLE
- [ ] Grounded explanations (no hallucinated facts)

### M3-6 to M3-9: Telegram Bot Core + Commands
- [ ] aiogram setup, `/start` (deep link), `/help`, `/feed`, `/saved`, `/settings`
- [ ] Inline keyboard: "View", "Save", "Apply"
- [ ] Rate limiting: 20 msg/min per user

### M3-10 to M3-16: Next.js Web Dashboard
- [ ] Pages: `/` (feed), `/explore` (search), `/opportunity/{slug}` (detail), `/saved`, `/applied`, `/profile`, `/settings`
- [ ] Components: opportunity cards, evidence trace, eligibility badge
- [ ] API integration: fetch from FastAPI

**M3 Exit Criteria:**
- Recommendation p95 < 5s fresh, < 200ms cached
- Telegram p95 < 5s normal path
- INELIGIBLE never recommended
- Explanations grounded (verifiable)

---

## M4 — Feedback Learning & Notifications (9 tasks)

### M4-1 to M4-3: Behavior Aggregation + Feedback Agent + Preference Update
- [ ] Aggregate `user_events` → behavior profile
- [ ] LangGraph Feedback Agent: LOAD_BEHAVIOR → PATTERNS → SIGNAL_QUALITY → ESTIMATE → INSIGHT → VALIDATE → APPLY/NO-UPDATE/HOLD
- [ ] Budget: 8 steps, 2 LLM calls, 20s
- [ ] Versioned preference updates (evidence-backed, confidence ≥0.7)

### M4-4: Feedback Agent Task
- [ ] arq cron: daily per active user
- [ ] Skip if events < 5 (insufficient signal)

### M4-5 to M4-7: Notification System
- [ ] Schedule reminders: D-3, D-1, urgent (<24h)
- [ ] `dispatch_notifications_task`: arq cron 07:00 WIB
- [ ] Rate limit (20 msg/min/user), idempotency keys
- [ ] Respect `user_preferences.notification_settings`

### M4-8 to M4-9: Explicit Feedback + Behavior Influence
- [ ] `/feedback` endpoint + Telegram command: "relevant", "not relevant"
- [ ] `user_events` type `feedback` recorded
- [ ] Behavior → ranking influence (A/B test-able)

**M4 Exit Criteria:**
- Feedback Agent produces versioned insights with evidence
- Low-confidence signal → NO-UPDATE (no garbage)
- Behavior influences ranking (measured)
- No duplicate notifications (idempotent)

---

## M5 — Discovery & Recovery (8 tasks)

### M5-1 to M5-3: Recovery Agent + Source Health
- [ ] LangGraph Recovery: DIAGNOSE → SELECT_STRATEGY → EXECUTE → VALIDATE → SUCCESS/RETRY/DEGRADED/PAUSE
- [ ] Budget: 2 attempts, 8 steps, 3 LLM calls, 60s
- [ ] Source health: 3 errors → degraded, 5 → paused

### M5-4 to M5-7: Discovery Agent + Search Adapter + Admin
- [ ] LangGraph Discovery: PLAN_SEARCH → SEARCH → INSPECT → EVALUATE → REGISTER → VALIDATE
- [ ] Budget: 10 steps, 2 LLM calls, 90s
- [ ] Search adapter: SearXNG / configurable
- [ ] Admin: approve/reject source proposals

**M5 Exit Criteria:**
- Recovery success ≥60% recoverable failures
- Agent budget exhaustion <10%
- Discovery produces source candidates (PENDING_REVIEW, not auto-active)
- Source health auto-degrade/pause

---

## M6 — Beta Hardening (10 tasks)

### M6-1 to M6-5: Observability + Security + Retention
- [ ] Structured logging (structlog)
- [ ] Agent metrics dashboard (SQL views)
- [ ] Admin alerting (daily check → Telegram)
- [ ] Data retention cron (30-90 days)
- [ ] Security audit: RLS, rate limiting, input validation, secrets scan

### M6-6 to M6-10: Load Test + E2E + Docs + Demo
- [ ] Load test: 100 concurrent users, 300 opportunities
- [ ] E2E tests (Playwright)
- [ ] Open source docs: README, CONTRIBUTING, ARCHITECTURE, .env example, LICENSE
- [ ] Demo mode: `make demo` offline (Ollama)
- [ ] Beta metrics: Precision@5, CTR, save rate, apply rate

**M6 Exit Criteria:**
- All quality targets Tech Spec §32 measured
- Fresh clone → running < 5 min
- E2E tests passing
- No secrets in repo
- Beta ready: 100+ users capacity

---

## Estimated Effort Summary

| Milestone | Tasks | Effort |
|---|---|---|
| M0 | 11 | ~1.5 weeks ✅ |
| M1 | 16 | ~4 weeks |
| M2 | 11 | ~2.5 weeks |
| M3 | 16 | ~4 weeks |
| M4 | 9 | ~2 weeks |
| M5 | 8 | ~2.5 weeks |
| M6 | 10 | ~2.5 weeks |
| **Total** | **81** | **~19 weeks** |

With parallelization M4/M5: ~16 weeks.

---

## Next Actions

1. **M1-8:** Implement LLM extraction service
2. **M1-9 to M1-16:** Complete extraction pipeline + agent + fixture corpus
3. **M2:** User + matching
4. **M3→M6:** Recommendation, action, feedback, discovery, hardening

**Git commits recommended at:**
- M1 complete (extraction pipeline end-to-end working)
- M2 complete (user + matching testable)
- M3 complete (Telegram + web working, recommendation ranked)
- M4 complete (behavior influences ranking)
- M5 complete (discovery + recovery agents bounded)
- M6 complete (beta ready)
