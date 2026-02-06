.PHONY: up down logs migrate seed test lint format clean

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
