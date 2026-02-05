-- Phase2 initial schema (from Alembic 001)

create schema if not exists phase2;

create table if not exists phase2.raw_files (
  id uuid primary key,
  source varchar(50) not null,
  original_name varchar(255) not null,
  sha256 varchar(64) not null,
  stored_path text not null,
  acquired_at timestamptz,
  metadata_json jsonb,
  created_at timestamptz default now()
);

create unique index if not exists uq_raw_files_sha256
  on phase2.raw_files (sha256);

create table if not exists phase2.documents (
  id uuid primary key,
  country varchar(2) not null,
  doc_number varchar(20) not null,
  kind varchar(10),
  publication_date date,
  raw_file_id uuid references phase2.raw_files(id),
  created_at timestamptz default now(),
  updated_at timestamptz
);

create unique index if not exists uq_documents_country_number_kind
  on phase2.documents (country, doc_number, kind);

create table if not exists phase2.claims (
  id uuid primary key,
  document_id uuid not null references phase2.documents(id),
  claim_no integer not null,
  claim_text text not null,
  created_at timestamptz default now(),
  updated_at timestamptz
);

create unique index if not exists uq_claims_document_claim_no
  on phase2.claims (document_id, claim_no);

create table if not exists phase2.ingest_runs (
  id uuid primary key,
  run_type varchar(20) not null,
  started_at timestamptz,
  finished_at timestamptz,
  status varchar(20) not null default 'running',
  detail_json jsonb
);

create index if not exists ix_documents_country_doc_number
  on phase2.documents (country, doc_number);

create index if not exists ix_claims_document_id
  on phase2.claims (document_id);
