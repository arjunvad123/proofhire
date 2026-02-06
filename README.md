# ProofHire

B2B SaaS that helps startup founders hire the right software engineers by replacing low-signal resumes with company-calibrated, standardized work simulations and proof-gated candidate briefs.

## Core Principles

- **Evidence-first**: Every claim shown to a founder must be backed by artifacts (diffs, test logs, metrics, writeups)
- **Fail-closed**: If a claim can't be proven by rules over evidence, it's labeled UNPROVEN with recommended interview questions
- **No hire/no-hire automation**: We provide decision support (briefs + evidence), not auto-decisions
- **No sensitive attribute inference**: System must not infer or use protected attributes

## Architecture

```
proofhire/
├── backend/       # FastAPI + Postgres + Redis + Proof Engine
├── runner/        # Background worker + Docker sandbox for simulations
├── web/           # Next.js frontend
└── docker-compose.yml
```

### System Flow

```
Founder creates role → COM + Rubric generated
                              ↓
Candidate applies → Starts simulation → Docker sandbox executes
                                              ↓
                                    Runner collects artifacts
                                              ↓
                              Backend: evidence → claims → proof engine
                                              ↓
                                    Brief generated with
                                    proven/unproven claims
                                              ↓
                              Founder reviews brief with evidence
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### First-time Setup

```bash
# 1. Build the sandbox image (runs simulations)
make build-sandbox

# 2. Start infrastructure services
docker-compose up -d postgres redis minio

# 3. Wait for services to be healthy, then run migrations
sleep 5
docker-compose run --rm backend alembic upgrade head

# 4. Start all services
docker-compose up
```

Or use the all-in-one setup command:

```bash
make setup
make up
```

### Access the App

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Development

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Run with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd web
npm install

# Copy environment template
cp .env.example .env.local

# Run dev server
npm run dev
```

### Runner

```bash
cd runner
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the worker
python -m runner
```

### Sandbox Image

The runner executes simulations in isolated Docker containers:

```bash
# Build the sandbox image
make build-sandbox

# Or manually:
docker build -t proofhire-sandbox:latest ./runner/sandbox
```

## Testing

```bash
# Backend tests
cd backend && pytest

# With coverage
cd backend && pytest --cov=app --cov-report=html

# Frontend tests
cd web && npm test
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | View service logs |
| `make setup` | First-time setup (build sandbox, migrate) |
| `make build-sandbox` | Build sandbox Docker image |
| `make migrate` | Run database migrations |
| `make test` | Run backend tests |
| `make clean` | Remove all containers and caches |

## API Documentation

Once running, visit http://localhost:8000/docs for the interactive OpenAPI documentation.

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Register a new user |
| `POST /api/auth/login` | Login and get JWT |
| `POST /api/orgs` | Create organization |
| `POST /api/roles` | Create hiring role |
| `POST /api/applications/{id}/runs` | Start simulation |
| `GET /api/applications/{id}/brief` | Get candidate brief |

## Environment Variables

See the `.env.example` files in each service directory:
- `backend/.env.example`
- `runner/.env.example`
- `web/.env.example`

## License

Proprietary
