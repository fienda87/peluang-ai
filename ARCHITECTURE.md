# Peluang.ai — Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    EXPERIENCE LAYER                      │
│   Next.js Dashboard          Telegram Bot (aiogram)     │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│                    API / TRANSPORT                       │
│              FastAPI + Pydantic + JWT                    │
│   /auth  /opportunities  /recommendations  /events      │
│   /admin /healthz                                       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  APPLICATION SERVICES                    │
│  IngestionService  RecommendationService  BehaviorSvc   │
│  FeedbackService   NotificationService   AnalyticsSvc   │
└──────────────────────────┬──────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌──────────────────┐ ┌──────────┐ ┌──────────────────┐
│  DOMAIN SERVICES │ │  AGENTS  │ │  INFRASTRUCTURE  │
│  Eligibility     │ │ LangGraph│ │  PostgreSQL      │
│  Matching        │ │ 5 agents │ │  Redis           │
│  Deduplication   │ │ bounded  │ │  Object Storage  │
│  Validation      │ │ budgets  │ │  OCR / Vision    │
└──────────────────┘ └──────────┘ └──────────────────┘
```

## The 5 Agents

| Agent | Purpose | Budget (steps/LLM/time) |
|---|---|---|
| Discovery | Find candidate opportunities/sources | 10 / 2 / 90s |
| Extraction | HTML/PDF/image → structured data | 8 / 2 / 60s |
| Recovery | Recover failed extractions | 8 / 3 / 60s |
| Recommendation | Contextual ranking + explanation | 6 / 2 / 15s |
| Feedback | Behavior → preference signals | 8 / 2 / 20s |

All agents: default-deny tools, no direct DB access, auditable via `agent_runs` + `agent_run_events`.

## Data Flow

```
Sources → Fetch → Detect Type → Extract (deterministic → LLM → Vision)
  → Validate → Deduplicate → Upsert Opportunity → Embed
  → Match → Rank → Recommend → User
  → Behavior Events → Feedback Agent → Preference Update → Better Ranking
```

## Key Design Decisions

1. **Deterministic-first**: Regex/rule parsers before LLM. LLM only for semantic ambiguity.
2. **3-state eligibility**: ELIGIBLE / INELIGIBLE / UNKNOWN. Never silently drop ambiguous cases.
3. **Bounded agents**: Hard budgets on steps, LLM calls, runtime. Budget exhaustion is terminal.
4. **Provider-neutral AI**: OpenRouter primary, Ollama fallback. Swap via config.
5. **Modular monolith**: No microservices. Domain modules with clear boundaries.
6. **arq over Celery**: Native asyncio, lighter, fits MVP scale. (ADR-001)
7. **pgvector exact search**: No HNSW until scale demands it.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI, Pydantic v2 |
| Database | PostgreSQL 15 + pgvector + pg_trgm |
| Queue | Redis + arq |
| Agents | LangGraph |
| Frontend | Next.js 14 (App Router) |
| Telegram | aiogram 3.x |
| AI | OpenRouter / Ollama |
| OCR | Tesseract (local) |
| Testing | pytest, Playwright |
| Lint | ruff |
