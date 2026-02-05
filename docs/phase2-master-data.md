# Phase2 会社・製品マスタ設計（MVP）

作成日: 2026-02-05  
対象: リポジトリルート（Supabase Postgres + Supabase Storage）

## 目的
特許侵害調査に必要な会社・製品情報を継続収集し、証跡付きでDBに蓄積する。  
特許DBと安全に紐づけ、検索で即時に候補抽出できる状態を作る。

## スキーマ概要
既存 `phase2` スキーマに **追加・拡張** する。削除はしない。

## マイグレーション方針
- **Supabase migrations を正とする。**
- Alembic は履歴保持のみ（新規変更は Supabase に集約）。

### companies 拡張
- `corporate_number`（法人番号）
- `country`, `legal_type`
- `normalized_name`
- `address_raw`, `address_pref`, `address_city`
- `status`, `is_listed`, `has_jp_entity`
- `website_url`, `contact_url`

### company_aliases 拡張
- `alias_type`, `language`, `source_evidence_id`

### company_identifiers 新規
- `company_id`, `id_type`, `value`, `source_evidence_id`

### products 拡張
- `model_number`, `category_path`, `description`, `sale_region`
- `normalized_name`, `status`

### product_identifiers 新規
- `product_id`, `id_type`, `value`, `source_evidence_id`

### evidence 拡張（証跡）
- `source_type`, `captured_at`
- `content_hash`, `content_type`, `storage_path`

### 会社/製品/特許リンク 新規
- `company_evidence_links`
- `product_evidence_links`
- `company_product_links`
- `patent_company_links`
  - `review_status` / `review_note` を保持

### analysis_jobs 拡張
- `company_id`, `product_id`

## API 仕様（MVP）

### 会社
- `POST /v1/companies`
- `GET /v1/companies/{company_id}`
- `GET /v1/companies/search?q=...`
- `POST /v1/companies/{company_id}/aliases`
- `POST /v1/companies/{company_id}/identifiers`
- `POST /v1/companies/{company_id}/evidence`

### 製品
- `POST /v1/products`
- `GET /v1/products/{product_id}`
- `GET /v1/products/search?q=...`
- `POST /v1/products/{product_id}/identifiers`
- `POST /v1/products/{product_id}/evidence`

### リンク
- `POST /v1/links/company-product`
- `POST /v1/links/patent-company`
- `GET /v1/links/review-queue`
- `POST /v1/links/company-product/{link_id}/review`
- `POST /v1/links/patent-company/{link_id}/review`

### 証跡
- `POST /v1/evidence`（base64 + content_type）

## 運用メモ
- Supabase Storage を証跡保存先とする。
- `content_hash` で改ざん検知を行う。
- `link_type=probabilistic` はレビューキューに必ず入れる。
- レビュー結果は `review_status` に `approved` / `rejected` を保存。

## 注意点
- 本リポジトリは **本番DBを開発でも使用**。  
  マイグレーション実行や破壊的DB操作は必ず事前承認が必要。
