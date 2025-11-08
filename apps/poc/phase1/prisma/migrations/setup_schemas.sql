-- ============================================
-- スキーマリセット & 再作成スクリプト
-- ============================================

-- 1. 既存テーブルを削除
DROP TABLE IF EXISTS public.analysis_jobs_local CASCADE;
DROP TABLE IF EXISTS local.analysis_jobs CASCADE;
DROP TABLE IF EXISTS production.analysis_jobs CASCADE;

-- 2. 既存スキーマを削除
DROP SCHEMA IF EXISTS local CASCADE;
DROP SCHEMA IF EXISTS production CASCADE;

-- 3. スキーマを作成
CREATE SCHEMA local;
CREATE SCHEMA production;

-- 4. localスキーマにテーブル作成
CREATE TABLE local.analysis_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),

  -- ジョブステータス
  status TEXT NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,

  -- 入力データ
  patent_number TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  company_name TEXT NOT NULL,
  product_name TEXT NOT NULL,

  -- Deep Research結果
  openai_response_id TEXT,
  input_prompt TEXT,
  research_results JSONB,

  -- 分析結果
  requirements JSONB,
  compliance_results JSONB,
  summary JSONB,

  -- メタデータ
  user_id UUID,
  ip_address TEXT
);

-- 5. productionスキーマにテーブル作成
CREATE TABLE production.analysis_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ(6) NOT NULL DEFAULT NOW(),

  -- ジョブステータス
  status TEXT NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,

  -- 入力データ
  patent_number TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  company_name TEXT NOT NULL,
  product_name TEXT NOT NULL,

  -- Deep Research結果
  openai_response_id TEXT,
  input_prompt TEXT,
  research_results JSONB,

  -- 分析結果
  requirements JSONB,
  compliance_results JSONB,
  summary JSONB,

  -- メタデータ
  user_id UUID,
  ip_address TEXT
);

-- 6. インデックス作成（local）
CREATE INDEX idx_jobs_status ON local.analysis_jobs(status);
CREATE INDEX idx_jobs_created_at ON local.analysis_jobs(created_at DESC);
CREATE INDEX idx_jobs_user_id ON local.analysis_jobs(user_id);

-- 7. インデックス作成（production）
CREATE INDEX idx_jobs_status ON production.analysis_jobs(status);
CREATE INDEX idx_jobs_created_at ON production.analysis_jobs(created_at DESC);
CREATE INDEX idx_jobs_user_id ON production.analysis_jobs(user_id);

-- 8. 確認
SELECT 'local.analysis_jobs' as table_name, COUNT(*) as count FROM local.analysis_jobs
UNION ALL
SELECT 'production.analysis_jobs' as table_name, COUNT(*) as count FROM production.analysis_jobs;
