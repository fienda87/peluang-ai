# Contributing to Peluang.ai

Thanks for your interest in contributing! This guide gets you set up.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- (Optional) Ollama for local LLM inference

## Setup

```bash
git clone https://github.com/yourname/peluang-ai.git
cd peluang-ai
cp .env.example .env   # edit with your keys

# Backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -e ".[dev,ingestion]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev,ingestion]"  # Linux/Mac

# Frontend
cd ../frontend
npm install
```

## Running Locally

```bash
# Infrastructure
docker compose up -d postgres redis

# Migrations + seed
cd backend && alembic upgrade head && python -m scripts.seed

# API server
uvicorn app.main:app --reload --port 8000

# Worker (separate terminal)
python -m arq app.workers.settings.WorkerSettings

# Frontend (separate terminal)
cd frontend && npm run dev
```

## Code Style

- Python: `ruff check .` and `ruff format .` (line length 100)
- TypeScript: Next.js defaults
- No comments unless requested
- Follow existing module patterns in `app/modules/`

## Architecture Rules

- Agents NEVER access the database directly — use module services
- Deterministic logic first, LLM only when reasoning is needed
- All agent runs are bounded (steps, LLM calls, runtime)
- Tool permissions are default-deny per agent
- Domain code must not import FastAPI, Celery/arq, LangGraph, or provider SDKs

## Testing

```bash
cd backend
pytest -v                    # unit + fixture tests
ruff check .                 # lint

cd frontend/e2e
npx playwright test          # E2E (requires running app)
```

## Commit Convention

```
M<milestone>-<task>: Short description

# Examples:
M1-7: Deterministic extractor with Indonesian date parsing
M3-5: Telegram bot /start deep link handler
```

## Pull Request Process

1. Fork and create a branch from `main`
2. Make changes with tests
3. Ensure `ruff check .` and `pytest -v` pass
4. Submit PR with clear description

## License

By contributing, you agree your contributions are licensed under MIT.
