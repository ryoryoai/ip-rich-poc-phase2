# Case Management

## Overview

Investigation cases represent a unit of patent infringement investigation work. Each case tracks the investigation from initial draft through to confirmed findings or archival.

## Case Workflow

```
draft -> exploring -> reviewing -> confirmed -> archived
```

| Status | Description |
|--------|-------------|
| `draft` | Case created, not yet started |
| `exploring` | Active investigation, running analysis |
| `reviewing` | Results under expert review |
| `confirmed` | Findings confirmed |
| `archived` | Investigation complete or abandoned |

## Data Model

### investigation_cases

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key |
| `tenant_id` | uuid | Tenant FK |
| `title` | text | Case title |
| `description` | text | Case description |
| `status` | text | Workflow status |
| `assignee_id` | uuid | Assigned user |
| `patent_id` | uuid | Primary patent under investigation |

### case_targets

Links a case to multiple investigation targets (patents, products, companies).

| Column | Type | Description |
|--------|------|-------------|
| `case_id` | uuid | FK to investigation_cases |
| `target_type` | text | 'patent', 'product', or 'company' |
| `target_id` | uuid | UUID of the target entity |

### match_candidates

Patent x Product candidate pairs with scoring.

| Column | Type | Description |
|--------|------|-------------|
| `patent_id` | uuid | FK to patents |
| `product_id` | uuid | FK to products |
| `company_id` | uuid | FK to companies |
| `score_total` | float | Overall score |
| `score_coverage` | float | Claim coverage score |
| `score_evidence_quality` | float | Evidence quality score |
| `score_blackbox_penalty` | float | Blackbox penalty |
| `score_legal_status` | float | Legal status bonus |
| `status` | text | candidate/reviewing/confirmed/dismissed |
| `analysis_job_id` | uuid | Source analysis job |

### case_matches

Links match candidates to investigation cases.

| Column | Type | Description |
|--------|------|-------------|
| `case_id` | uuid | FK to investigation_cases |
| `match_candidate_id` | uuid | FK to match_candidates |
| `reviewer_note` | text | Reviewer's note |

## API Endpoints

### Cases

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/cases` | Create case |
| `GET` | `/v1/cases` | List cases (status filter, pagination) |
| `GET` | `/v1/cases/{id}` | Case detail with targets and matches |
| `PATCH` | `/v1/cases/{id}` | Update case (title, description, status) |
| `POST` | `/v1/cases/{id}/targets` | Add investigation target |
| `GET` | `/v1/cases/{id}/matches` | List case matches |
| `POST` | `/v1/cases/{id}/matches` | Link match candidate |

### Match Candidates

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/matches` | List candidates (patent/product/company filter) |
| `GET` | `/v1/matches/{id}` | Candidate detail with score breakdown |
| `PATCH` | `/v1/matches/{id}` | Update status |

## Frontend Pages

- `/cases` - Case list with status filtering
- `/cases/new` - Create new case
- `/cases/{case_id}` - Case detail with targets, matches, and status progression
