-- Add claim_nos column to analysis_jobs for multi-claim processing
ALTER TABLE phase2.analysis_jobs
  ADD COLUMN IF NOT EXISTS claim_nos jsonb DEFAULT NULL;

COMMENT ON COLUMN phase2.analysis_jobs.claim_nos IS
  'JSON array of claim numbers to analyze. NULL = all claims.';
