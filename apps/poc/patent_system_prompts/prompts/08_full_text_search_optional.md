# 08 追加プロンプト（任意）: claim全文検索エンドポイント

PostgreSQL全文検索を使い、claims.claim_text を検索できる API を追加してください。

## 仕様
- GET /v1/search/claims?q=...&limit=...
- 返却: document識別子、claim_no、スニペット（任意）、スコア（任意）

## 実装
- DB側: GIN(to_tsvector('japanese', claim_text)) を使う案を優先
- アプリ側: SQLAlchemy で tsquery を組み立て
- SQLインジェクションに注意

## テスト
- フィクスチャに含まれる単語で検索し、少なくとも1件ヒットすること
