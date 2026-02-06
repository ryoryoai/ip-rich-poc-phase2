-- Phase 1B: Case Management - Investigation cases, match candidates
-- Depends on: 20260208000000_phase1a_foundation.sql (tenants table)

-- =============================================================================
-- 1. investigation_cases (案件)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.investigation_cases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001',
  title text NOT NULL,
  description text,
  status text NOT NULL DEFAULT 'draft',
    -- draft, exploring, reviewing, confirmed, archived
  assignee_id uuid,
  patent_id uuid REFERENCES phase2.patents(internal_patent_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_investigation_cases_tenant
  ON phase2.investigation_cases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_investigation_cases_status
  ON phase2.investigation_cases(status);
CREATE INDEX IF NOT EXISTS idx_investigation_cases_patent
  ON phase2.investigation_cases(patent_id);
CREATE INDEX IF NOT EXISTS idx_investigation_cases_created_at
  ON phase2.investigation_cases(created_at);

COMMENT ON TABLE phase2.investigation_cases IS 'Investigation case for patent infringement analysis';

-- =============================================================================
-- 2. case_targets (案件の調査対象)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.case_targets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES phase2.investigation_cases(id) ON DELETE CASCADE,
  target_type text NOT NULL,  -- 'patent', 'product', 'company'
  target_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_case_targets_case
  ON phase2.case_targets(case_id);
CREATE INDEX IF NOT EXISTS idx_case_targets_target
  ON phase2.case_targets(target_type, target_id);

COMMENT ON TABLE phase2.case_targets IS 'Targets (patent/product/company) associated with a case';

-- =============================================================================
-- 3. match_candidates (特許×製品の候補)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.match_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001',
  patent_id uuid NOT NULL REFERENCES phase2.patents(internal_patent_id),
  product_id uuid REFERENCES phase2.products(id),
  company_id uuid REFERENCES phase2.companies(id),

  -- Score breakdown (06_search_and_ranking.md)
  score_total float,
  score_coverage float,
  score_evidence_quality float,
  score_blackbox_penalty float,
  score_legal_status float,

  logic_version text DEFAULT 'v1',
  analysis_job_id uuid REFERENCES phase2.analysis_jobs(id),
  status text DEFAULT 'candidate',  -- candidate, reviewing, confirmed, dismissed
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_match_candidates_tenant
  ON phase2.match_candidates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_match_candidates_patent
  ON phase2.match_candidates(patent_id);
CREATE INDEX IF NOT EXISTS idx_match_candidates_product
  ON phase2.match_candidates(product_id);
CREATE INDEX IF NOT EXISTS idx_match_candidates_company
  ON phase2.match_candidates(company_id);
CREATE INDEX IF NOT EXISTS idx_match_candidates_score
  ON phase2.match_candidates(score_total DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_match_candidates_status
  ON phase2.match_candidates(status);

COMMENT ON TABLE phase2.match_candidates IS 'Patent x Product match candidate with score breakdown';

-- =============================================================================
-- 4. case_matches (案件↔候補の紐づけ)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.case_matches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES phase2.investigation_cases(id) ON DELETE CASCADE,
  match_candidate_id uuid NOT NULL REFERENCES phase2.match_candidates(id),
  reviewer_note text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_case_matches_case
  ON phase2.case_matches(case_id);
CREATE INDEX IF NOT EXISTS idx_case_matches_candidate
  ON phase2.case_matches(match_candidate_id);

COMMENT ON TABLE phase2.case_matches IS 'Links investigation cases to match candidates';
