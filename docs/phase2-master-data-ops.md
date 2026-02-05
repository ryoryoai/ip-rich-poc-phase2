# Phase2 マスタデータ運用手順（DB変更）

作成日: 2026-02-05  
対象: `apps/poc/phase2` / Supabase Postgres

## 前提
- **本番DBを開発/検証でも利用**する設計。  
  マイグレーション実行は必ず事前承認が必要。
- 破壊的操作（DROP/DELETE/TRUNCATE/RESET）は禁止。

## 適用対象マイグレーション
- Supabase migrations: `supabase/migrations/`
  - `20260205100000_phase2_schema_baseline.sql`（production schema のスナップショット）
  - `20260205131000_phase2_texts_keywords_profile.sql`
  - `20260205132000_phase2_patent_text_storage.sql`
  - `20260205133000_phase2_jp_index.sql`
  - **Alembicは今後使用しない（履歴は保持）**

## 適用手順（承認後）
1. **事前確認**
   - 影響範囲の共有（テーブル追加/カラム追加のみ）
   - Supabaseバックアップ/スナップショット取得
2. **接続確認**
   - `DATABASE_URL` が **本番** を指しているか確認
   - `DIRECT_URL` が設定されているか確認
3. **マイグレーション実行（Supabase）**
   - `supabase db push`
4. **検証**
   - 新規テーブル作成の確認
   - 追加カラムの存在確認
   - 簡易APIテスト（/v1/companies, /v1/products, /v1/links/review-queue）

## ロールバック（原則不要）
破壊的操作を避けるため、**ロールバックは非推奨**。  
どうしても必要な場合のみ SupabaseのSQL実行で個別対応し、事前承認を取ること。

## 監査ログ
- いつ、誰が、どのマイグレーションを実行したかを記録する。
