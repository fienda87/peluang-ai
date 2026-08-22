.PHONY: setup dev up down logs migrate seed test lint format clean

setup:
	cp -n .env.example .env || true
	docker compose build

dev: up

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f api worker

migrate:
	docker compose run --rm api alembic upgrade head

migrate-local:
	cd backend && alembic upgrade head

seed:
	docker compose run --rm api python -m scripts.seed

test:
	cd backend && pytest -v

lint:
	cd backend && ruff check .

format:
	cd backend && ruff format . && ruff check --fix .

clean:
	docker compose down -v
