.PHONY: up down logs backend frontend ingest eval test lint clean corpus-hash

# === Local dev ===
up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f backend

# === Backend ===
backend-install:
	cd backend && pip install -e ".[dev]"

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

lint:
	cd backend && ruff check app/ && mypy app/ --ignore-missing-imports
	cd frontend && npm run lint

test:
	cd backend && pytest -q

# === Pipelines ===
ingest:
	cd backend && python -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json

ingest-dry:
	cd backend && python -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --dry-run

reindex:
	cd backend && python -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --reindex

eval:
	cd backend && python -m app.eval.ragas_eval --golden ../eval/golden_set.json --out ../eval/report.json

corpus-hash:
	cd corpus && git log --oneline -1 -- sources/ 2>/dev/null || echo "no-git"; find sources -type f -exec sha256sum {} \; | sort | sha256sum | cut -c1-12

# === DB ===
migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(msg)"

# === Frontend ===
frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
