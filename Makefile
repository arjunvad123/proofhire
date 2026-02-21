.PHONY: up down logs migrate seed test lint format clean test-gateway

# Docker commands
up:
	docker-compose up -d
down:
	docker-compose down

logs:
	docker-compose logs -f

# Database commands
migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(name)"

seed:
	cd backend && python -m app.db.seed

# Development
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-web:
	cd web && npm run dev

dev-runner:
	cd runner && python -m runner

# Testing
test:
	cd backend && pytest -v

test-cov:
	cd backend && pytest --cov=app --cov-report=html

# Linting & formatting
lint:
	cd backend && ruff check .
	cd web && npm run lint

format:
	cd backend && ruff format .
	cd web && npm run format

# Cleanup
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf backend/.coverage backend/htmlcov
	rm -rf web/.next web/node_modules

# Build
build:
	docker-compose build

build-sandbox:
	docker build -t proofhire-sandbox:latest ./runner/sandbox

# Setup everything for first run
setup: build-sandbox
	docker-compose up -d postgres redis minio
	sleep 5
	docker-compose run --rm backend alembic upgrade head
	@echo "Setup complete! Run 'make up' to start all services."

# Install dependencies
install:
	cd backend && pip install -e ".[dev]"
	cd web && npm install

# ── Agencity + OpenClaw ──────────────────────────────────────────────────

# Clone and build OpenClaw as embedded dependency
setup-openclaw:
	cd agencity && ./scripts/setup-openclaw.sh

# Update OpenClaw to latest release
update-openclaw:
	cd agencity && ./scripts/update-openclaw.sh

# Start Agencity (API + OpenClaw gateway)
agencity-start:
	cd agencity && ./bin/agencity start

# Stop Agencity
agencity-stop:
	cd agencity && ./bin/agencity stop

# Agencity health check
agencity-doctor:
	cd agencity && ./bin/agencity doctor

# Start only the Agencity API (no OpenClaw)
agencity-api:
	cd agencity && python -m uvicorn app.main:app --reload --port 8001

# Run OpenClaw gateway integration tests
OPENCLAW_DIR := agencity/vendor/openclaw
VITEST := $(shell ls -d $(OPENCLAW_DIR)/node_modules/.pnpm/vitest@*/node_modules/vitest/vitest.mjs 2>/dev/null | head -1)
OPENCLAW_TOKEN := $(shell node -e "try{const c=require('fs').readFileSync(process.env.HOME+'/.openclaw/openclaw.json','utf8');const j=JSON.parse(c);console.log(j.gateway?.auth?.token??'')}catch(e){}" 2>/dev/null)

test-gateway:
	@echo "Running OpenClaw gateway integration tests..."
	@if [ -z "$(VITEST)" ]; then echo "ERROR: vitest not found in $(OPENCLAW_DIR)/node_modules — run 'make setup-openclaw' first"; exit 1; fi
	cd $(OPENCLAW_DIR) && \
		OPENCLAW_GATEWAY_AUTH_TOKEN="$(OPENCLAW_TOKEN)" \
		ANTHROPIC_API_KEY="$$(grep ANTHROPIC_API_KEY ./../.env 2>/dev/null | cut -d= -f2- || echo $$ANTHROPIC_API_KEY)" \
		node "$(abspath $(VITEST))" run test/agencity-gateway.test.ts --reporter=verbose
