# Legacy Migrations

This folder keeps older Supabase migration files for reference only.
They are **not** applied by Supabase tooling because they are outside
`supabase/migrations/`.

The current source of truth is:
- `supabase/migrations/20260205100000_phase2_schema_baseline.sql`
- `supabase/migrations/20260205131000_phase2_texts_keywords_profile.sql`
- `supabase/migrations/20260205132000_phase2_patent_text_storage.sql`

Notes:
- JP Index schema is already included in the baseline snapshot; legacy JP Index
  migrations are kept here only for traceability.
