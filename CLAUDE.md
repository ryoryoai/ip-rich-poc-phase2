# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Patent infringement analysis system (Phase2 only):
- FastAPI + SQLAlchemy backend (repo root)
- Next.js frontend (`frontend/`)
- Supabase migrations in `supabase/migrations/` (source of truth)

## Key Commands

### API (repo root)

```bash
# Python venv
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Apply migrations (Supabase SQL in supabase/migrations)
# See docs/phase2-master-data-ops.md

# Start API server
python -m app.cli serve

# CLI pipeline
python -m app.cli ingest --path ./data/raw
python -m app.cli parse --all
python -m app.cli runs list

# Quality checks
ruff check .
ruff format .
mypy app
pytest
```

### Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev              # http://localhost:3002
npm run build
npm run start
npm run lint
npm run type-check
```

## Architecture

### Pipeline

- A: Fetch/Store/Normalize
- B: Discovery
- C: Analyze

### Storage

- Supabase PostgreSQL with schema `phase2` (via `options=-csearch_path=phase2` in `DATABASE_URL` / `DIRECT_URL`).
- Raw files stored under `RAW_STORAGE_PATH`.

## Important Notes

### Port Configuration

- Phase2 API: `API_PORT` (default **8000**)
- Phase2 Frontend: Port **3002**

### Environment Variables (Phase2)

```bash
# Supabase PostgreSQL (schema=phase2)
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://...

# Storage
RAW_STORAGE_PATH=./data/raw

# API
API_HOST=0.0.0.0
API_PORT=8000

# LLM Provider
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Prompts directory
PROMPTS_DIR=./prompts

# Cron secret (for Vercel Cron authentication)
CRON_SECRET=your-secret
```

### Database Safety

This repo uses the production DB for dev/test. Avoid destructive DB operations and require explicit approval before running schema changes or deletes.

## Common Development Tasks

- API endpoints: `app/api/v1/endpoints/`
- DB models: `app/db/models.py`
- Migrations: `supabase/migrations/` (source of truth); `alembic/` is legacy history
- CLI pipeline: `app/cli.py`
- Frontend: `frontend/`
  - Supabase migration history alignment: `supabase/migrations/20251207091828_legacy.sql` and `20251207091940_legacy.sql` are placeholders to match remote history; do not delete unless remote history is updated.
  - Supabase CLI reads repo root `.env.local` and can fail to parse Vercel-created values. If `supabase link/db push` fails with an env parse error, temporarily move `.env.local` aside and rerun.

## Running Phase2 Locally

1. Copy `.env.example` to `.env` and fill keys.
2. Create venv and install dependencies.
3. Apply Supabase migrations (`supabase/migrations/`).
4. Start API server: `python -m app.cli serve`.
5. Start frontend: `cd frontend && npm run dev`.
