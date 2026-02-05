-- Phase2 analysis tables (from Alembic 002)

CREATE SCHEMA IF NOT EXISTS phase2;

CREATE TABLE IF NOT EXISTS phase2.analysis_jobs (
  id uuid PRIMARY KEY,
  patent_id varchar(30) NOT NULL,
  target_product text,
  pipeline varchar(20) NOT NULL,
  status varchar(20) NOT NULL DEFAULT 'pending',
  current_stage varchar(50),
  created_at timestamptz DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz,
  error_message text,
  context_json jsonb
);

CREATE TABLE IF NOT EXISTS phase2.analysis_results (
  id uuid PRIMARY KEY,
  job_id uuid NOT NULL REFERENCES phase2.analysis_jobs(id),
  stage varchar(50) NOT NULL,
  input_data jsonb,
  output_data jsonb,
  llm_model varchar(50),
  tokens_input integer,
  tokens_output integer,
  latency_ms integer,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_analysis_jobs_patent_id
  ON phase2.analysis_jobs (patent_id);

CREATE INDEX IF NOT EXISTS ix_analysis_jobs_status
  ON phase2.analysis_jobs (status);

CREATE INDEX IF NOT EXISTS ix_analysis_results_job_id
  ON phase2.analysis_results (job_id);
