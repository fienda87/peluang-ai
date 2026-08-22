# Setup Guide — API Keys & Integrations

## 1. OpenRouter API Key (LLM)

Peluang.ai uses OpenRouter as the primary LLM gateway (free models available).

1. Go to https://openrouter.ai and create an account
2. Navigate to **Keys** → https://openrouter.ai/keys
3. Click **Create Key**, give it a name (e.g. `peluang-dev`)
4. Copy the key (starts with `sk-or-`)
5. Add to `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxx
   ```

### Free models (no cost)
| Purpose | Model ID |
|---|---|
| Chat / Extraction | `meta-llama/llama-3.1-8b-instruct:free` |
| Vision (poster OCR fallback) | `google/gemini-flash-1.5` |
| Embeddings | `openai/text-embedding-3-small` |

### Ollama (fully local, no API key needed)
```bash
# Install: https://ollama.com
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# .env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## 2. Telegram Bot Token

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Choose a display name (e.g. `Peluang AI`)
4. Choose a username ending in `bot` (e.g. `peluang_ai_bot`)
5. BotFather returns a token like `7123456789:AAH1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6`
6. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=7123456789:AAH1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6
   ```
7. Set the webhook (after API is running):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://yourdomain.com/telegram/webhook"
   ```
   For local dev, use polling instead (set `TELEGRAM_USE_POLLING=true`).

### Telegram deep link (account linking)
The web app generates a one-time link token. User clicks:
```
https://t.me/peluang_ai_bot?start=<link_token>
```
The bot's `/start` handler reads the token and links the Telegram account to the user.

## 3. PostgreSQL + Redis (Docker)

No API keys needed. Just run:
```bash
docker compose up -d postgres redis
```

Default credentials (dev only):
- Postgres: `peluang` / `peluang_dev` on port `5432`
- Redis: `localhost:6379`

## 4. Verify Everything

```bash
# Backend health
curl http://localhost:8000/healthz
# → {"status":"ok"}

# Frontend
cd frontend && npm run dev
# → http://localhost:3000

# Worker
cd backend && python -m arq app.workers.settings.WorkerSettings
# → "worker_started" in logs
```

## 5. Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | (see .env.example) | PostgreSQL async connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis for arq task queue |
| `JWT_SECRET` | Yes | — | Secret for JWT signing. Use a long random string |
| `AI_PROVIDER` | No | `openrouter` | `openrouter` or `ollama` |
| `OPENROUTER_API_KEY` | If openrouter | — | OpenRouter API key |
| `AI_CHAT_MODEL` | No | `meta-llama/llama-3.1-8b-instruct:free` | Chat/extraction model |
| `AI_VISION_MODEL` | No | `google/gemini-flash-1.5` | Vision model for poster OCR fallback |
| `AI_EMBEDDING_MODEL` | No | `openai/text-embedding-3-small` | Embedding model |
| `OLLAMA_BASE_URL` | If ollama | `http://localhost:11434` | Ollama server URL |
| `TELEGRAM_BOT_TOKEN` | For Telegram | — | Bot token from @BotFather |
| `WEB_BASE_URL` | No | `http://localhost:3000` | Frontend URL for deep links |
| `STORAGE_BACKEND` | No | `local` | `local` filesystem storage |
| `STORAGE_LOCAL_PATH` | No | `./data/storage` | Local storage directory |
