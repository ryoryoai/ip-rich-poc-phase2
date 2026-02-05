-- Phase2 auto-collection scaffolding (company/product identity, field evidence, collection jobs)

CREATE SCHEMA IF NOT EXISTS phase2;

-- Company identity (法人番号中心のID設計)
ALTER TABLE IF EXISTS phase2.companies
  ADD COLUMN IF NOT EXISTS identity_type varchar(20) NOT NULL DEFAULT 'provisional',
  ADD COLUMN IF NOT EXISTS identity_confidence double precision NOT NULL DEFAULT 50;

CREATE INDEX IF NOT EXISTS idx_companies_identity_type
  ON phase2.companies (identity_type);

CREATE INDEX IF NOT EXISTS idx_companies_identity_confidence
  ON phase2.companies (identity_confidence);

-- Field-level evidence/history for companies
CREATE TABLE IF NOT EXISTS phase2.company_field_values (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES phase2.companies(id),
  field_name varchar(64) NOT NULL,
  value_text text,
  value_json jsonb,
  value_hash varchar(64),
  source_evidence_id uuid REFERENCES phase2.evidence(id),
  source_type varchar(30),
  source_ref text,
  confidence_score double precision,
  captured_at timestamptz,
  is_current boolean NOT NULL DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_company_field_values_dedup
  ON phase2.company_field_values (company_id, field_name, value_hash)
  WHERE value_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_company_field_values_company
  ON phase2.company_field_values (company_id);

CREATE INDEX IF NOT EXISTS idx_company_field_values_current
  ON phase2.company_field_values (company_id, field_name, is_current);

-- Field-level evidence/history for products
CREATE TABLE IF NOT EXISTS phase2.product_field_values (
  id uuid PRIMARY KEY,
  product_id uuid NOT NULL REFERENCES phase2.products(id),
  field_name varchar(64) NOT NULL,
  value_text text,
  value_json jsonb,
  value_hash varchar(64),
  source_evidence_id uuid REFERENCES phase2.evidence(id),
  source_type varchar(30),
  source_ref text,
  confidence_score double precision,
  captured_at timestamptz,
  is_current boolean NOT NULL DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_product_field_values_dedup
  ON phase2.product_field_values (product_id, field_name, value_hash)
  WHERE value_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_product_field_values_product
  ON phase2.product_field_values (product_id);

CREATE INDEX IF NOT EXISTS idx_product_field_values_current
  ON phase2.product_field_values (product_id, field_name, is_current);

-- Generic collection jobs (company/product ingestion, web/pdf, public data, etc.)
CREATE TABLE IF NOT EXISTS phase2.collection_jobs (
  job_id uuid PRIMARY KEY,
  job_type varchar(30) NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'queued',
  priority integer NOT NULL DEFAULT 5,
  retry_count integer NOT NULL DEFAULT 0,
  max_retries integer NOT NULL DEFAULT 3,
  error_code varchar(50),
  error_detail text,
  metrics_json jsonb,
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_collection_jobs_status
  ON phase2.collection_jobs (status);

CREATE INDEX IF NOT EXISTS idx_collection_jobs_created_at
  ON phase2.collection_jobs (created_at);

CREATE TABLE IF NOT EXISTS phase2.collection_items (
  item_id uuid PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES phase2.collection_jobs(job_id),
  entity_type varchar(20) NOT NULL,
  entity_id uuid,
  source_type varchar(30),
  source_ref text,
  status varchar(20) NOT NULL DEFAULT 'queued',
  retry_count integer NOT NULL DEFAULT 0,
  error_code varchar(50),
  error_detail text,
  payload_json jsonb,
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_collection_items_job
  ON phase2.collection_items (job_id);

CREATE INDEX IF NOT EXISTS idx_collection_items_status
  ON phase2.collection_items (status);
