-- Phase2 review status columns for link tables (from Alembic 004)

CREATE SCHEMA IF NOT EXISTS phase2;

ALTER TABLE IF EXISTS phase2.company_product_links
  ADD COLUMN IF NOT EXISTS review_status varchar(20) NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS review_note text;

ALTER TABLE IF EXISTS phase2.patent_company_links
  ADD COLUMN IF NOT EXISTS review_status varchar(20) NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS review_note text;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'phase2' AND table_name = 'company_product_links'
  ) THEN
    UPDATE phase2.company_product_links
      SET review_status = 'approved'
      WHERE link_type = 'deterministic' AND review_status = 'pending';
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'phase2' AND table_name = 'patent_company_links'
  ) THEN
    UPDATE phase2.patent_company_links
      SET review_status = 'approved'
      WHERE link_type = 'deterministic' AND review_status = 'pending';
  END IF;
END $$;
