# ProofHire

B2B SaaS that helps startup founders hire the right software engineers by replacing low-signal resumes with company-calibrated, standardized work simulations and proof-gated candidate briefs.

## Core Principles

- **Evidence-first**: Every claim shown to a founder must be backed by artifacts (diffs, test logs, metrics, writeups)
- **Fail-closed**: If a claim can't be proven by rules over evidence, it's labeled UNPROVEN with recommended next steps
- **No hire/no-hire automation**: We provide decision support (briefs + evidence), not auto-decisions
- **No sensitive attribute inference**: System must not infer or use protected attributes

## Architecture

```
proofhire/
├── backend/     # FastAPI + Postgres + Redis
├── runner/      # Docker sandbox for simulations
├── web/         # Next.js frontend
└── docker-compose.yml
```

## Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
make migrate

# Seed test data (optional)
make seed

# Access the app
open http://localhost:3000
```

## Development

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd web
npm install
npm run dev
```

### Runner

```bash
cd runner
pip install -r requirements.txt
python runner.py
```

## Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd web && npm test
```

## API Documentation

Once running, visit http://localhost:8000/docs for the interactive API documentation.

## License

Proprietary
