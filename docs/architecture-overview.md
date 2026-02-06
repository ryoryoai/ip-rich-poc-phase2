# Architecture Overview

## System Purpose

Patent infringement investigation platform. Automates candidate discovery, evidence collection, and claim chart generation to support expert review. Does NOT make final infringement determinations.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + SQLAlchemy |
| Database | PostgreSQL (Supabase, schema `phase2`) |
| Frontend | Next.js (App Router) + shadcn/ui + Tailwind |
| Auth | Supabase Auth (approval-based gating) |
| LLM | OpenAI / Anthropic (configurable via `LLM_PROVIDER`) |
| Migrations | Raw SQL in `supabase/migrations/` |

## Pipeline Architecture

Three-stage pipeline with progressive depth:

```
Stage A: Fetch/Store/Normalize
  - Patent data ingestion (JP standard data, bulk + API)
  - Company/product master data
  - Document storage and text extraction

Stage B: Discovery
  - Tech keyword extraction
  - Company-patent linking
  - Product-company linking

Stage C: Analyze (per-claim)
  - Stage 10: Claim element extraction
  - Stage 11: Evidence query generation
  - Stage 12: Product fact extraction
  - Stage 13: Element assessment (batch per claim)
  - Stage 14: Claim decision aggregation
  - Stage 15: Case summary
  - Stage 16: Investigation task generation
```

## Data Flow

```
Patent Number -> [Stage A] -> Patent Master + Claims
                                     |
Product/Company -> [Stage B] -> Links + Keywords
                                     |
Analysis Request -> [Stage C] -> Per-claim results
                                     |
                    [Case Mgmt] -> Investigation Case
                                     |
                    [Match]     -> Match Candidates (scored)
```

## Key Directories

```
app/
  api/v1/endpoints/   # FastAPI route handlers
  db/models.py        # SQLAlchemy ORM (all tables)
  services/           # Business logic
    analysis_service.py   # Pipeline execution
    case_service.py       # Case management
    audit_service.py      # Audit logging
  llm/                # LLM integration
prompts/              # YAML prompt templates
  c_analyze/          # Stage C prompts
supabase/migrations/  # SQL migrations (source of truth)
frontend/
  src/app/            # Next.js pages
  src/lib/            # API client, types, utilities
  src/components/     # UI components
docs/
  iprich_spec/        # Full system specification
```

## Spec-to-Code Mapping

| Spec Phase | Spec Doc | Implementation Status |
|------------|----------|----------------------|
| Phase 0: Repo/CI | - | Done (monorepo, Vercel) |
| Phase 1: Patent DB | 05_ingestion | Done (patents, versions, claims) |
| Phase 2: Text/Docs | 05_ingestion | Partial (claims done, doc chunks TODO) |
| Phase 3: Recall | 06_search_ranking | TODO (hybrid search) |
| Phase 4: Precision | 07_evidence_chart | Partial (Stage C analysis, claim chart TODO) |
| Phase 5: Case Mgmt | 09_ui_spec | Done (investigation_cases, match_candidates) |
| Phase 6: Monitoring | 01_requirements FR-09 | TODO |

## Multi-Tenant Design

Minimal implementation: `tenant_id` column on core tables (`patents`, `companies`, `products`, `analysis_jobs`, `documents`, `investigation_cases`, `match_candidates`). Default tenant UUID: `a0000000-0000-0000-0000-000000000001`. No UI/RBAC for tenant switching yet.

## Audit Logging

Generic `audit_logs` table tracks entity operations. Used by `AuditService` to record create/update/delete/export/approve actions with JSON diffs.
