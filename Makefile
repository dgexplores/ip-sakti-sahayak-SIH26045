.PHONY: up down logs backend backend-install backend-run lint test typecheck eval check \
        ingest ingest-dry reindex corpus-hash frontend-install frontend-dev frontend-build clean

# === Interpreter ===
# Every backend target goes through these so the gates can run against an
# explicit interpreter instead of whatever `python` happens to resolve to.
# Override when the venv is not activated:
#   make eval PYTHON=backend/.venv/bin/python
PYTHON ?= python
PYTEST ?= pytest

# === Local dev ===
# .env is gitignored and only .env.example is committed, so `make up` used to
# fail on a fresh clone with "env file .env not found" — on the documented
# primary path. The prerequisite creates it on first use.
.env:
	cp .env.example .env
	@echo "created .env from .env.example (free defaults, nothing to edit for a demo)"

up: .env
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f backend

# === Backend ===
backend-install:
	cd backend && $(PYTHON) -m pip install -e ".[dev]"

backend-run:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

typecheck:
	cd backend && $(PYTHON) -m mypy app/ --ignore-missing-imports

lint:
	cd backend && $(PYTHON) -m ruff check app/
	cd frontend && npm run lint -- --max-warnings=0

test:
	cd backend && $(PYTEST) -q

# === Pipelines ===
ingest:
	cd backend && $(PYTHON) -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json

ingest-dry:
	cd backend && $(PYTHON) -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --dry-run

reindex:
	cd backend && $(PYTHON) -m app.pipelines.ingest.cli --manifest ../corpus/manifest.json --reindex

# Exits non-zero when any metric fails, so this is a real gate rather than a
# report nobody reads.
eval:
	cd backend && $(PYTHON) -m app.eval.ragas_eval --golden ../eval/golden_set.json --out ../eval/report.json

corpus-hash:
	cd backend && $(PYTHON) -c "from app.core.corpus import corpus_version, corpus_document_count as n; print(corpus_version(), f'({n()} documents)')"

# Everything that has to be true before a demo, in one command.
check: test eval check-i18n check-frontend
	@echo "all checks passed"

# === Frontend ===
frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npx tsc --noEmit && npm run build

# These two read frontend/ and need node >= 22 for type stripping. They run
# without a frontend install; only check-frontend needs one, and it says so
# rather than failing obscurely if typescript is missing.
NODE_FLAGS = --experimental-strip-types --disable-warning=MODULE_TYPELESS_PACKAGE_JSON

check-i18n:
	node $(NODE_FLAGS) eval/check_i18n.ts

check-frontend:
	node $(NODE_FLAGS) eval/check_frontend_syntax.ts

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
