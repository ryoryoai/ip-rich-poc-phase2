# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An automated patent infringement investigation system with two main components:
1. **Documentation Site** (`docs-site/`): Docusaurus-based documentation with AWS CloudFront and flexible authentication (none, basic, Cognito, IP restriction)
2. **Patent Analysis System Phase2** (`apps/poc/phase2/`): FastAPI + SQLAlchemy backend with Supabase migrations and a Next.js frontend (`apps/poc/phase2/frontend/`)

## Key Commands

### Documentation Site (`docs-site/`)

```bash
cd docs-site
npm install              # Install dependencies
npm start                # Dev server on http://localhost:1919 (custom port!)
npm run build            # Production build
npm run serve            # Serve production build on http://localhost:1919
npm run typecheck        # TypeScript type checking
npm run format           # Format with Prettier
npm run format:check     # Check Prettier formatting

# PlantUML Diagrams
npm run diagrams:generate  # Generate all diagrams
npm run diagrams:current   # Generate current-workflow.svg
npm run diagrams:automated # Generate automated-workflow.svg
npm run diagrams:dataflow  # Generate data-flow.svg
```

### Phase2 API (`apps/poc/phase2/`)

```bash
cd apps/poc/phase2

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

### Phase2 Frontend (`apps/poc/phase2/frontend/`)

```bash
cd apps/poc/phase2/frontend
npm install
npm run dev              # http://localhost:3002
npm run build
npm run start
npm run lint
npm run type-check
```

### Infrastructure (`infra/`)

Use mise for consistent Terraform (1.9.8) and Node.js (20) versions:

```bash
cd infra
mise trust              # Trust configuration
mise install            # Install tools
mise run lambda-install # Install Lambda@Edge dependencies (for Cognito auth)
mise run init           # terraform init
mise run plan           # terraform plan
mise run apply          # terraform apply
mise run validate       # terraform validate
mise run fmt            # terraform fmt
```

## Architecture

### Phase2 Pipeline (`apps/poc/phase2/`)

- **A: Fetch/Store/Normalize**: Retrieve patent data, normalize, and persist.
- **B: Discovery**: Generate search seeds and rank candidate products.
- **C: Analyze**: Decompose claims and assess infringement.

### Storage

- Supabase PostgreSQL with schema `phase2` (via `options=-csearch_path=phase2` in `DATABASE_URL` / `DIRECT_URL`).
- Raw files stored under `RAW_STORAGE_PATH`.

## Important Notes

### Port Configuration

- **Docusaurus dev server**: Port **1919**
- **Phase2 API**: `API_PORT` (default **8000**)
- **Phase2 Frontend**: Port **3002**

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

### Terraform State Operations

Per global CLAUDE.md: Avoid `terraform state rm/mv/import` without explicit user approval. Use standard Terraform workflow:
1. Modify `.tf` files
2. `mise run plan` to review changes
3. `mise run apply` after approval

## Common Development Tasks

- API endpoints: `apps/poc/phase2/app/api/v1/endpoints/`
- DB models: `apps/poc/phase2/app/db/models.py`
- Migrations: `supabase/migrations/` (source of truth); `apps/poc/phase2/alembic/` is legacy history
- CLI pipeline: `apps/poc/phase2/app/cli.py`
- Frontend: `apps/poc/phase2/frontend/`
  - Supabase migration history alignment: `supabase/migrations/20251207091828_legacy.sql` and `20251207091940_legacy.sql` are placeholders to match remote history; do not delete unless remote history is updated.
  - Supabase CLI reads repo root `.env.local` and can fail to parse Vercel-created values. If `supabase link/db push` fails with an env parse error, temporarily move `.env.local` aside and rerun.

## Running Phase2 Locally

1. Copy `apps/poc/phase2/.env.example` to `apps/poc/phase2/.env` and fill keys.
2. Create venv and install dependencies.
3. Apply Supabase migrations (`supabase/migrations/`).
4. Start API server: `python -m app.cli serve`.
5. Start frontend: `cd apps/poc/phase2/frontend && npm run dev`.
