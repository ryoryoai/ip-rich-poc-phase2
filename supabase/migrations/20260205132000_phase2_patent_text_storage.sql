-- Phase2 patent text storage tables and raw file metadata (from Alembic 005)

CREATE SCHEMA IF NOT EXISTS phase2;

ALTER TABLE IF EXISTS phase2.raw_files
  ADD COLUMN IF NOT EXISTS storage_provider varchar(20),
  ADD COLUMN IF NOT EXISTS bucket varchar(100),
  ADD COLUMN IF NOT EXISTS object_path text,
  ADD COLUMN IF NOT EXISTS mime_type varchar(100),
  ADD COLUMN IF NOT EXISTS size_bytes bigint,
  ADD COLUMN IF NOT EXISTS etag varchar(100);

CREATE TABLE IF NOT EXISTS phase2.patents (
  internal_patent_id uuid PRIMARY KEY,
  jurisdiction varchar(2) NOT NULL DEFAULT 'JP',
  application_no varchar(40),
  publication_no varchar(40),
  registration_no varchar(40),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_patents_application_no
  ON phase2.patents (jurisdiction, application_no)
  WHERE application_no IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_patents_publication_no
  ON phase2.patents (jurisdiction, publication_no)
  WHERE publication_no IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_patents_registration_no
  ON phase2.patents (jurisdiction, registration_no)
  WHERE registration_no IS NOT NULL;

CREATE TABLE IF NOT EXISTS phase2.patent_number_sources (
  id uuid PRIMARY KEY,
  internal_patent_id uuid NOT NULL REFERENCES phase2.patents(internal_patent_id),
  number_type varchar(20) NOT NULL,
  number_value_raw text NOT NULL,
  number_value_norm text,
  source_type varchar(20) NOT NULL,
  source_ref text,
  retrieved_at timestamptz,
  confidence double precision
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_patent_number_sources
  ON phase2.patent_number_sources (
    internal_patent_id,
    number_type,
    number_value_raw,
    source_type
  );

CREATE INDEX IF NOT EXISTS idx_patent_number_sources_patent
  ON phase2.patent_number_sources (internal_patent_id);

CREATE TABLE IF NOT EXISTS phase2.patent_versions (
  version_id uuid PRIMARY KEY,
  internal_patent_id uuid NOT NULL REFERENCES phase2.patents(internal_patent_id),
  publication_type varchar(20) NOT NULL,
  kind_code varchar(10),
  gazette_number varchar(40),
  issue_date date,
  language varchar(8) DEFAULT 'ja',
  source_type varchar(20) NOT NULL,
  source_ref text,
  raw_file_id uuid REFERENCES phase2.raw_files(id),
  raw_object_uri text,
  content_hash varchar(64),
  parse_status varchar(20),
  parse_result_json jsonb,
  norm_version varchar(20),
  is_latest boolean NOT NULL DEFAULT false,
  acquired_at timestamptz,
  created_at timestamptz DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_patent_versions_hash
  ON phase2.patent_versions (internal_patent_id, publication_type, content_hash)
  WHERE content_hash IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_patent_versions_latest
  ON phase2.patent_versions (internal_patent_id, publication_type)
  WHERE is_latest IS TRUE;

CREATE INDEX IF NOT EXISTS idx_patent_versions_internal
  ON phase2.patent_versions (internal_patent_id);

CREATE TABLE IF NOT EXISTS phase2.patent_claims (
  id uuid PRIMARY KEY,
  version_id uuid NOT NULL REFERENCES phase2.patent_versions(version_id),
  claim_no integer NOT NULL,
  text_raw text NOT NULL,
  text_norm text,
  norm_version varchar(20)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_patent_claims_version_claim_no
  ON phase2.patent_claims (version_id, claim_no);

CREATE INDEX IF NOT EXISTS idx_patent_claims_version
  ON phase2.patent_claims (version_id);

CREATE TABLE IF NOT EXISTS phase2.patent_spec_sections (
  id uuid PRIMARY KEY,
  version_id uuid NOT NULL REFERENCES phase2.patent_versions(version_id),
  section_type varchar(40) NOT NULL,
  order_no integer NOT NULL,
  text_raw text NOT NULL,
  text_norm text,
  norm_version varchar(20)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_patent_spec_sections_version_section_order
  ON phase2.patent_spec_sections (version_id, section_type, order_no);

CREATE INDEX IF NOT EXISTS idx_patent_spec_sections_version
  ON phase2.patent_spec_sections (version_id);

CREATE TABLE IF NOT EXISTS phase2.ingestion_jobs (
  job_id uuid PRIMARY KEY,
  status varchar(20) NOT NULL DEFAULT 'queued',
  priority integer NOT NULL DEFAULT 5,
  force_refresh boolean NOT NULL DEFAULT false,
  source_preference varchar(20),
  idempotency_key varchar(80),
  retry_count integer NOT NULL DEFAULT 0,
  max_retries integer NOT NULL DEFAULT 3,
  error_code varchar(50),
  error_detail text,
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_jobs_idempotency_key
  ON phase2.ingestion_jobs (idempotency_key);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status
  ON phase2.ingestion_jobs (status);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_created_at
  ON phase2.ingestion_jobs (created_at);

CREATE TABLE IF NOT EXISTS phase2.ingestion_job_items (
  job_item_id uuid PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES phase2.ingestion_jobs(job_id),
  internal_patent_id uuid REFERENCES phase2.patents(internal_patent_id),
  input_number text NOT NULL,
  input_number_type varchar(20) NOT NULL,
  status varchar(20) NOT NULL,
  retry_count integer NOT NULL DEFAULT 0,
  error_code varchar(50),
  error_detail text,
  target_version_hint jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ingestion_job_items
  ON phase2.ingestion_job_items (job_id, input_number, input_number_type);

CREATE INDEX IF NOT EXISTS idx_ingestion_job_items_job
  ON phase2.ingestion_job_items (job_id);
