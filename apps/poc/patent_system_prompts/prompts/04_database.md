# 04 実装プロンプト: DBスキーマとモデルを完成させる

SQLAlchemyモデルとAlembicマイグレーションを整備してください。

## テーブル
- raw_files
- documents
- claims
- ingest_runs

## documents の一意性
- (country, doc_number, kind) にユニーク制約
- raw_file_id を外部キーとして保持（どのRawから生成されたか追える）

## claims の一意性
- (document_id, claim_no) にユニーク制約

## 型
- claim_text は TEXT
- metadata_json/detail_json は JSONB

## インデックス
- documents: (country, doc_number, kind)
- claims: (document_id, claim_no)

## 追加（任意）
- claims.claim_text の全文検索インデックス（GIN to_tsvector）

## 成果物
- Alembicの初期マイグレーションが一発で作れる状態
- READMEにマイグレーション手順
