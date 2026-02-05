# 00 Master Prompt: 特許データ保存システム（JP中心）を一括生成する

あなたはシニアソフトウェアエンジニア兼SREです。以下の仕様に従って、動作するリポジトリ一式を生成してください。
出力は、実装ファイル（コード、設定、README、テスト）で構成してください。

## 目的
- 入力: 日本の特許番号（例: 特許第1234567号 / 1234567 / JP1234567B2 など）
- 出力: 請求項1の全文（正規化済みテキスト）と最小限の書誌情報
- データは自前で保存し、外部サイトへの都度アクセスを前提にしない

## 範囲（MVP）
1) Raw格納
- ダウンロード済み（または手元に配置済み）のZIP/XMLを、不変（イミュータブル）に保存
- 取得元、配布日、チェックサム（SHA-256）、保存パス（オブジェクトキー）をメタデータ化

2) パースと抽出
- 公報XMLから以下を抽出してDBへ格納
  - 文献識別: country=JP, doc_number（登録番号 or 公開番号）, kind（B1/B2/A 等）
  - 請求項: claim_no と claim_text（請求項1は必須）
- 文字コードは XML宣言を尊重（EUC-JP等の可能性あり）

3) API
- FastAPI
- 主要エンドポイント
  - GET /healthz
  - GET /v1/patents/{patent_id}/claims/1
  - GET /v1/patents/resolve?input=...   （入力表記揺れを受け、内部IDへ解決）
- 返却は JSON。claim_text には改行を含めてよい

4) CLI（運用）
- Typer で以下を提供
  - ingest: Raw取り込み（ローカルディレクトリ or URLリスト読み込み）
  - parse: RawからパースしてDBに反映
  - serve: API起動（開発用）
- ingest/parse は冪等（同じRawや同じ文献を重複登録しない）

5) DB
- PostgreSQL
- SQLAlchemy + Alembic
- テーブル案（必要に応じて増やしてよい）
  - raw_files(id, source, original_name, sha256, stored_path, acquired_at, metadata_json)
  - documents(id, country, doc_number, kind, publication_date, raw_file_id, created_at, updated_at)
  - claims(id, document_id, claim_no, claim_text, created_at, updated_at)
  - ingest_runs(id, started_at, finished_at, status, detail_json)

6) テスト
- pytest
- XMLフィクスチャ（小さめでよい）を用意し、claim1抽出が通ること
- APIの統合テスト（TestClient）で /claims/1 が返ること

7) ローカル実行
- ローカル開発向け

## 制約
- 外部サイトのスクレイピングに依存しない（MVPでは「ローカルに置かれた公報ZIP/XML」を ingest できればよい）
- 例外系（claim1欠落、XML不正、重複）をログに残す
- 重要な設定は環境変数 or .env で

## 望ましいリポジトリ構成（例）
- app/
  - api/
  - core/
  - db/
  - ingest/
  - parse/
- scripts/
- tests/
- README.md

## 実装の品質要求
- 型ヒントを付ける
- ログを丁寧に（構造化ログが望ましい）
- エラーは握りつぶさず、APIは適切なステータスを返す
- 依存関係は最小限で、READMEにセットアップ手順を書く

## 追加（任意）
- PostgreSQLの全文検索（GIN）で claim_text を検索できるエンドポイントを追加してよい（MVP後でも可）

生成後、次を必ず提示してください:
- 実行手順（CLI）
- サンプル入力と期待出力
- 主要ファイル一覧
