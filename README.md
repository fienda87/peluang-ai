# Peluang.ai

Personal Opportunity Intelligence Platform for Indonesian students.

Find opportunities worth your time — beasiswa, lomba, magang, fellowship, and more.

## Quick Start (< 5 minutes)

```bash
# 1. Clone & setup
git clone https://github.com/yourname/peluang-ai.git
cd peluang-ai
cp .env.example .env

# 2. Start infrastructure
docker compose up -d postgres redis

# 3. Run migrations
make migrate

# 4. Seed sample data
make seed

# 5. Start API + worker
docker compose up -d api worker

# 6. Verify
curl http://localhost:8000/healthz
```

## Development (without Docker)

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check .

# Migrations (local)
alembic upgrade head
```

## Architecture

- **Backend:** Python + FastAPI (modular monolith)
- **Task queue:** arq + Redis
- **Database:** PostgreSQL 15 + pgvector + pg_trgm
- **Agents:** LangGraph (5 bounded agents: Discovery, Extraction, Recovery, Recommendation, Feedback)
- **Frontend:** Next.js (coming in M3)
- **Telegram:** aiogram 3.x (coming in M3)

## Project Structure

```
peluang-ai/
├── backend/
│   ├── app/
│   │   ├── api/            # HTTP routes
│   │   ├── modules/        # Domain modules (identity, opportunities, ingestion, etc.)
│   │   ├── agents/         # LangGraph agents (discovery, extraction, recovery, recommendation, feedback)
│   │   ├── infrastructure/ # DB, storage adapters
│   │   ├── shared/         # Config, logging
│   │   └── workers/        # arq tasks
│   ├── migrations/         # Alembic
│   ├── scripts/            # Seed, utilities
│   └── tests/
├── frontend/               # Next.js (M3)
├── config/                 # YAML configs (agents, app)
├── docker/                 # Dockerfiles
└── docs/adr/               # Architecture Decision Records
```

## Key Docs

- `docs/adr/` — Architecture decisions
- Implementation Plan: M0→M6 milestones

## License

MIT
