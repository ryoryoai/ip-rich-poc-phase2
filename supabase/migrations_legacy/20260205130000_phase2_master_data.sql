-- Phase2 master data + links (companies/products/evidence)
-- This migration is the Supabase source of truth going forward.

CREATE SCHEMA IF NOT EXISTS phase2;

-- companies
ALTER TABLE IF EXISTS phase2.companies
  ADD COLUMN IF NOT EXISTS corporate_number varchar(13),
  ADD COLUMN IF NOT EXISTS country varchar(2),
  ADD COLUMN IF NOT EXISTS legal_type varchar(50),
  ADD COLUMN IF NOT EXISTS normalized_name text,
  ADD COLUMN IF NOT EXISTS address_raw text,
  ADD COLUMN IF NOT EXISTS address_pref varchar(20),
  ADD COLUMN IF NOT EXISTS address_city varchar(50),
  ADD COLUMN IF NOT EXISTS status varchar(20),
  ADD COLUMN IF NOT EXISTS is_listed boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS has_jp_entity boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS website_url text,
  ADD COLUMN IF NOT EXISTS contact_url text;

CREATE UNIQUE INDEX IF NOT EXISTS uq_companies_corporate_number
  ON phase2.companies (corporate_number);
CREATE INDEX IF NOT EXISTS idx_companies_corporate_number
  ON phase2.companies (corporate_number);
CREATE INDEX IF NOT EXISTS idx_companies_normalized_name
  ON phase2.companies (normalized_name);

-- company_aliases
ALTER TABLE IF EXISTS phase2.company_aliases
  ADD COLUMN IF NOT EXISTS alias_type varchar(30),
  ADD COLUMN IF NOT EXISTS language varchar(8),
  ADD COLUMN IF NOT EXISTS source_evidence_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fk_company_aliases_source_evidence'
  ) THEN
    ALTER TABLE phase2.company_aliases
      ADD CONSTRAINT fk_company_aliases_source_evidence
      FOREIGN KEY (source_evidence_id) REFERENCES phase2.evidence(id);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_company_aliases_alias
  ON phase2.company_aliases (alias);

-- products
ALTER TABLE IF EXISTS phase2.products
  ADD COLUMN IF NOT EXISTS model_number text,
  ADD COLUMN IF NOT EXISTS category_path text,
  ADD COLUMN IF NOT EXISTS description text,
  ADD COLUMN IF NOT EXISTS sale_region text,
  ADD COLUMN IF NOT EXISTS normalized_name text,
  ADD COLUMN IF NOT EXISTS status varchar(20);

CREATE INDEX IF NOT EXISTS idx_products_model_number
  ON phase2.products (model_number);
CREATE INDEX IF NOT EXISTS idx_products_normalized_name
  ON phase2.products (normalized_name);

-- evidence (snapshots)
ALTER TABLE IF EXISTS phase2.evidence
  ADD COLUMN IF NOT EXISTS source_type varchar(50),
  ADD COLUMN IF NOT EXISTS captured_at timestamptz,
  ADD COLUMN IF NOT EXISTS content_hash varchar(64),
  ADD COLUMN IF NOT EXISTS content_type varchar(100),
  ADD COLUMN IF NOT EXISTS storage_path text;

CREATE INDEX IF NOT EXISTS idx_evidence_content_hash
  ON phase2.evidence (content_hash);

-- analysis_jobs links
ALTER TABLE IF EXISTS phase2.analysis_jobs
  ADD COLUMN IF NOT EXISTS company_id uuid,
  ADD COLUMN IF NOT EXISTS product_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_analysis_jobs_company'
  ) THEN
    ALTER TABLE phase2.analysis_jobs
      ADD CONSTRAINT fk_analysis_jobs_company
      FOREIGN KEY (company_id) REFERENCES phase2.companies(id);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_analysis_jobs_product'
  ) THEN
    ALTER TABLE phase2.analysis_jobs
      ADD CONSTRAINT fk_analysis_jobs_product
      FOREIGN KEY (product_id) REFERENCES phase2.products(id);
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_company_id
  ON phase2.analysis_jobs (company_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_product_id
  ON phase2.analysis_jobs (product_id);

-- company_identifiers
CREATE TABLE IF NOT EXISTS phase2.company_identifiers (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES phase2.companies(id),
  id_type varchar(30) NOT NULL,
  value varchar(100) NOT NULL,
  source_evidence_id uuid REFERENCES phase2.evidence(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_company_identifiers UNIQUE (company_id, id_type, value)
);
CREATE INDEX IF NOT EXISTS idx_company_identifiers_value
  ON phase2.company_identifiers (value);

-- product_identifiers
CREATE TABLE IF NOT EXISTS phase2.product_identifiers (
  id uuid PRIMARY KEY,
  product_id uuid NOT NULL REFERENCES phase2.products(id),
  id_type varchar(30) NOT NULL,
  value varchar(100) NOT NULL,
  source_evidence_id uuid REFERENCES phase2.evidence(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_product_identifiers UNIQUE (product_id, id_type, value)
);
CREATE INDEX IF NOT EXISTS idx_product_identifiers_value
  ON phase2.product_identifiers (value);

-- company_evidence_links
CREATE TABLE IF NOT EXISTS phase2.company_evidence_links (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES phase2.companies(id),
  evidence_id uuid NOT NULL REFERENCES phase2.evidence(id),
  purpose varchar(50),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_company_evidence_links UNIQUE (company_id, evidence_id, purpose)
);
CREATE INDEX IF NOT EXISTS idx_company_evidence_links_company
  ON phase2.company_evidence_links (company_id);

-- product_evidence_links
CREATE TABLE IF NOT EXISTS phase2.product_evidence_links (
  id uuid PRIMARY KEY,
  product_id uuid NOT NULL REFERENCES phase2.products(id),
  product_version_id uuid REFERENCES phase2.product_versions(id),
  evidence_id uuid NOT NULL REFERENCES phase2.evidence(id),
  purpose varchar(50),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_product_evidence_links UNIQUE (product_id, product_version_id, evidence_id)
);
CREATE INDEX IF NOT EXISTS idx_product_evidence_links_product
  ON phase2.product_evidence_links (product_id);

-- company_product_links
CREATE TABLE IF NOT EXISTS phase2.company_product_links (
  id uuid PRIMARY KEY,
  company_id uuid NOT NULL REFERENCES phase2.companies(id),
  product_id uuid NOT NULL REFERENCES phase2.products(id),
  role varchar(30) NOT NULL,
  link_type varchar(20) NOT NULL,
  confidence_score double precision,
  review_status varchar(20) NOT NULL DEFAULT 'pending',
  review_note text,
  evidence_json jsonb,
  verified_by text,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_company_product_links_company_product_role UNIQUE (company_id, product_id, role)
);
CREATE INDEX IF NOT EXISTS idx_company_product_links_company
  ON phase2.company_product_links (company_id);
CREATE INDEX IF NOT EXISTS idx_company_product_links_product
  ON phase2.company_product_links (product_id);

-- patent_company_links
CREATE TABLE IF NOT EXISTS phase2.patent_company_links (
  id uuid PRIMARY KEY,
  document_id uuid REFERENCES phase2.documents(id),
  patent_ref varchar(40),
  company_id uuid NOT NULL REFERENCES phase2.companies(id),
  role varchar(30) NOT NULL,
  link_type varchar(20) NOT NULL,
  confidence_score double precision,
  review_status varchar(20) NOT NULL DEFAULT 'pending',
  review_note text,
  evidence_json jsonb,
  verified_by text,
  verified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_patent_company_links_doc_patent_company_role UNIQUE (document_id, patent_ref, company_id, role)
);
CREATE INDEX IF NOT EXISTS idx_patent_company_links_company
  ON phase2.patent_company_links (company_id);
CREATE INDEX IF NOT EXISTS idx_patent_company_links_document
  ON phase2.patent_company_links (document_id);

-- Backfill deterministic links to approved
UPDATE phase2.company_product_links
  SET review_status = 'approved'
  WHERE link_type = 'deterministic' AND review_status = 'pending';

UPDATE phase2.patent_company_links
  SET review_status = 'approved'
  WHERE link_type = 'deterministic' AND review_status = 'pending';
