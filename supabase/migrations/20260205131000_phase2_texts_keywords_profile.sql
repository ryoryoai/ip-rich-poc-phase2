-- Phase2 document texts, tech keywords, and profile fields (from Alembic 005)

CREATE SCHEMA IF NOT EXISTS phase2;

ALTER TABLE IF EXISTS phase2.claims
  ADD COLUMN IF NOT EXISTS source varchar(30),
  ADD COLUMN IF NOT EXISTS is_current boolean NOT NULL DEFAULT true;

ALTER TABLE IF EXISTS phase2.claim_elements
  ADD COLUMN IF NOT EXISTS metadata_json json;

ALTER TABLE IF EXISTS phase2.companies
  ADD COLUMN IF NOT EXISTS business_description text,
  ADD COLUMN IF NOT EXISTS primary_products text,
  ADD COLUMN IF NOT EXISTS market_regions text;

ALTER TABLE IF EXISTS phase2.products
  ADD COLUMN IF NOT EXISTS brand_name text;

CREATE TABLE IF NOT EXISTS phase2.document_texts (
  id uuid PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES phase2.documents(id),
  text_type varchar(30) NOT NULL,
  language varchar(8),
  source varchar(30),
  is_current boolean NOT NULL DEFAULT true,
  text text NOT NULL,
  metadata_json json,
  created_at timestamptz,
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_document_texts_document
  ON phase2.document_texts (document_id);

CREATE INDEX IF NOT EXISTS idx_document_texts_type
  ON phase2.document_texts (text_type);

CREATE INDEX IF NOT EXISTS idx_document_texts_current
  ON phase2.document_texts (document_id, text_type, is_current);

CREATE TABLE IF NOT EXISTS phase2.tech_keywords (
  id uuid PRIMARY KEY,
  term text NOT NULL,
  language varchar(8) NOT NULL DEFAULT 'ja',
  normalized_term text,
  synonyms json,
  abbreviations json,
  domain text,
  notes text,
  source_evidence_id uuid REFERENCES phase2.evidence(id),
  created_at timestamptz,
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_tech_keywords_term
  ON phase2.tech_keywords (term);

CREATE INDEX IF NOT EXISTS idx_tech_keywords_language
  ON phase2.tech_keywords (language);
