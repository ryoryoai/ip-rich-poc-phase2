-- Phase 1A: Foundation - Tenants, Audit Logs, Claim Sets, tenant_id on core tables
-- This migration is additive only. No destructive changes.

-- =============================================================================
-- 1. tenants table
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text NOT NULL,
  settings jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_tenants_slug UNIQUE (slug)
);

COMMENT ON TABLE phase2.tenants IS 'Tenant (organisation) for multi-tenant isolation';

-- Insert default tenant (used by all existing data)
INSERT INTO phase2.tenants (id, name, slug)
VALUES ('a0000000-0000-0000-0000-000000000001', 'default', 'default')
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- 2. audit_logs table (generic, not JP-specific)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES phase2.tenants(id),
  actor_id uuid,
  action text NOT NULL,        -- 'create','update','delete','export','approve','reject'
  entity_type text NOT NULL,   -- 'case','evidence','claim_chart','report','match_candidate'
  entity_id uuid,
  diff jsonb,
  metadata jsonb DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant
  ON phase2.audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
  ON phase2.audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
  ON phase2.audit_logs(created_at);

COMMENT ON TABLE phase2.audit_logs IS 'Generic audit log for all entity operations';

-- =============================================================================
-- 3. claim_sets table (claim version management)
-- =============================================================================

CREATE TABLE IF NOT EXISTS phase2.claim_sets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  patent_id uuid NOT NULL REFERENCES phase2.patents(internal_patent_id),
  version_label text NOT NULL,          -- 'original', 'amended_2024', etc.
  source text,                           -- 'gazette', 'api', 'manual'
  effective_date date,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claim_sets_patent
  ON phase2.claim_sets(patent_id);

COMMENT ON TABLE phase2.claim_sets IS 'Version-managed set of claims for a patent';

-- =============================================================================
-- 4. claim_elements extensions
-- =============================================================================

ALTER TABLE phase2.claim_elements
  ADD COLUMN IF NOT EXISTS approval_status text DEFAULT 'draft';

ALTER TABLE phase2.claim_elements
  ADD COLUMN IF NOT EXISTS synonyms jsonb DEFAULT '[]';

ALTER TABLE phase2.claim_elements
  ADD COLUMN IF NOT EXISTS claim_set_id uuid REFERENCES phase2.claim_sets(id);

COMMENT ON COLUMN phase2.claim_elements.approval_status IS 'draft, approved, rejected';
COMMENT ON COLUMN phase2.claim_elements.synonyms IS 'JSON array of synonym strings';
COMMENT ON COLUMN phase2.claim_elements.claim_set_id IS 'FK to versioned claim set';

-- =============================================================================
-- 5. Add tenant_id to core tables (nullable with default)
-- =============================================================================

-- patents
ALTER TABLE phase2.patents
  ADD COLUMN IF NOT EXISTS tenant_id uuid
    REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001';

-- companies
ALTER TABLE phase2.companies
  ADD COLUMN IF NOT EXISTS tenant_id uuid
    REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001';

-- products
ALTER TABLE phase2.products
  ADD COLUMN IF NOT EXISTS tenant_id uuid
    REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001';

-- analysis_jobs
ALTER TABLE phase2.analysis_jobs
  ADD COLUMN IF NOT EXISTS tenant_id uuid
    REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001';

-- documents
ALTER TABLE phase2.documents
  ADD COLUMN IF NOT EXISTS tenant_id uuid
    REFERENCES phase2.tenants(id)
    DEFAULT 'a0000000-0000-0000-0000-000000000001';
