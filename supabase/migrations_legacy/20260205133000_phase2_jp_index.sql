-- Phase2 JP Patent Index schema (idempotent)
-- Source: docs/jp_index_schema.sql

CREATE SCHEMA IF NOT EXISTS phase2;

CREATE TABLE IF NOT EXISTS phase2.jp_audit_logs (
  id uuid PRIMARY KEY,
  action varchar(50) NOT NULL,
  resource_id varchar(64),
  request_path text,
  method varchar(10),
  client_ip varchar(64),
  user_agent text,
  payload_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jp_audit_logs_created_at ON phase2.jp_audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_jp_audit_logs_action ON phase2.jp_audit_logs (action);

CREATE TABLE IF NOT EXISTS phase2.jp_ingest_batches (
  id uuid PRIMARY KEY,
  source varchar(50) NOT NULL,
  run_type varchar(20) NOT NULL,
  update_date date,
  batch_key varchar(100) NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'running',
  started_at timestamptz,
  finished_at timestamptz,
  counts_json jsonb,
  metadata_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_ingest_batches_batch_key UNIQUE (batch_key)
);

CREATE INDEX IF NOT EXISTS idx_jp_ingest_batches_update_date ON phase2.jp_ingest_batches (update_date);

CREATE TABLE IF NOT EXISTS phase2.jp_ingest_batch_files (
  id uuid PRIMARY KEY,
  batch_id uuid NOT NULL REFERENCES phase2.jp_ingest_batches(id),
  raw_file_id uuid REFERENCES phase2.raw_files(id),
  file_sha256 varchar(64),
  original_name varchar(255),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_ingest_batch_files_batch_raw UNIQUE (batch_id, raw_file_id)
);

CREATE INDEX IF NOT EXISTS idx_jp_ingest_batch_files_raw_file ON phase2.jp_ingest_batch_files (raw_file_id);

CREATE TABLE IF NOT EXISTS phase2.jp_cases (
  id uuid PRIMARY KEY,
  country varchar(2) NOT NULL DEFAULT 'JP',
  application_number_raw varchar(40),
  application_number_norm varchar(40),
  filing_date date,
  title text,
  abstract text,
  current_status varchar(20),
  status_updated_at timestamptz,
  last_update_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_jp_cases_application_number_norm ON phase2.jp_cases (application_number_norm);
CREATE INDEX IF NOT EXISTS idx_jp_cases_status ON phase2.jp_cases (current_status);
CREATE INDEX IF NOT EXISTS idx_jp_cases_last_update_date ON phase2.jp_cases (last_update_date);

CREATE TABLE IF NOT EXISTS phase2.jp_documents (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  doc_type varchar(20) NOT NULL,
  publication_number_raw varchar(40),
  publication_number_norm varchar(40),
  patent_number_raw varchar(40),
  patent_number_norm varchar(40),
  kind varchar(10),
  publication_date date,
  raw_file_id uuid REFERENCES phase2.raw_files(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_jp_documents_publication_number_norm ON phase2.jp_documents (publication_number_norm);
CREATE INDEX IF NOT EXISTS idx_jp_documents_patent_number_norm ON phase2.jp_documents (patent_number_norm);

CREATE TABLE IF NOT EXISTS phase2.jp_number_aliases (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  document_id uuid REFERENCES phase2.jp_documents(id),
  number_type varchar(20) NOT NULL,
  number_raw varchar(40),
  number_norm varchar(40) NOT NULL,
  country varchar(2) NOT NULL DEFAULT 'JP',
  kind varchar(10),
  is_primary boolean DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_number_aliases_type_norm UNIQUE (number_type, number_norm)
);

CREATE INDEX IF NOT EXISTS idx_jp_number_aliases_number_norm ON phase2.jp_number_aliases (number_norm);

CREATE TABLE IF NOT EXISTS phase2.jp_applicants (
  id uuid PRIMARY KEY,
  name_raw text NOT NULL,
  name_norm text,
  normalize_confidence double precision,
  source varchar(20),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_jp_applicants_name_norm ON phase2.jp_applicants (name_norm);

CREATE TABLE IF NOT EXISTS phase2.jp_case_applicants (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  applicant_id uuid NOT NULL REFERENCES phase2.jp_applicants(id),
  role varchar(20) NOT NULL DEFAULT 'applicant',
  is_primary boolean DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_case_applicants_case_app_role UNIQUE (case_id, applicant_id, role)
);

CREATE INDEX IF NOT EXISTS idx_jp_case_applicants_case ON phase2.jp_case_applicants (case_id);

CREATE TABLE IF NOT EXISTS phase2.jp_classifications (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  type varchar(10) NOT NULL,
  code varchar(64) NOT NULL,
  version varchar(20),
  is_primary boolean DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_classifications_case_type_code UNIQUE (case_id, type, code)
);

CREATE INDEX IF NOT EXISTS idx_jp_classifications_type_code ON phase2.jp_classifications (type, code);

CREATE TABLE IF NOT EXISTS phase2.jp_status_events (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  event_date date,
  event_type varchar(40) NOT NULL,
  source varchar(40),
  payload_json jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_jp_status_events_case UNIQUE (case_id, event_type, event_date, source)
);

CREATE INDEX IF NOT EXISTS idx_jp_status_events_case_date ON phase2.jp_status_events (case_id, event_date);

CREATE TABLE IF NOT EXISTS phase2.jp_status_snapshots (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  status varchar(20) NOT NULL,
  derived_at timestamptz NOT NULL DEFAULT now(),
  logic_version varchar(20) NOT NULL DEFAULT 'v1',
  basis_event_ids jsonb,
  reason text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jp_status_snapshots_case ON phase2.jp_status_snapshots (case_id);

CREATE TABLE IF NOT EXISTS phase2.jp_search_documents (
  id uuid PRIMARY KEY,
  case_id uuid NOT NULL REFERENCES phase2.jp_cases(id),
  document_id uuid REFERENCES phase2.jp_documents(id),
  title text,
  abstract text,
  applicants_text text,
  classifications_text text,
  status varchar(20),
  publication_date date,
  tsv tsvector,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz,
  CONSTRAINT uq_jp_search_documents_case UNIQUE (case_id)
);

CREATE INDEX IF NOT EXISTS idx_jp_search_documents_status ON phase2.jp_search_documents (status);
CREATE INDEX IF NOT EXISTS idx_jp_search_documents_tsv ON phase2.jp_search_documents USING gin (tsv);
