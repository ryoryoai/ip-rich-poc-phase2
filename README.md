# Phase2 - Patent Infringement Analysis System

日本特許の請求項データを保存・分析するシステム。LLMを使った侵害分析パイプラインを搭載。

## 機能

- **特許データ保存**: XML/ZIPからの取り込み、請求項抽出
- **侵害分析パイプライン**:
  - A: Fetch/Store/Normalize - 特許データの取得・正規化
  - B: Discovery - 検索シード生成・候補ランキング
  - C: Analyze - 請求項分解・侵害判定
- **会社/製品マスタ（MVP）**: `docs/phase2-master-data.md` を参照
- **会社データソース（gBizINFO）**: `docs/gbizinfo.md` を参照
- **運用手順（DB変更）**: `docs/phase2-master-data-ops.md` を参照（Supabase migrations が正）

## ローカルセットアップ

```bash
# 仮想環境作成
python -m venv .venv

# アクティベート (Windows)
.venv\Scripts\activate

# アクティベート (Linux/Mac)
source .venv/bin/activate

# 依存関係インストール
pip install -e ".[dev]"

# 環境変数設定
cp .env.example .env
# .env を編集
```

## 環境変数

```bash
# Database (Supabase)
DATABASE_URL=postgresql://...
DIRECT_URL=postgresql://...

# Raw storage
RAW_STORAGE_PATH=./data/raw
BULK_ROOT_PATH=./data/bulk

# LLM Provider
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=evidence
SUPABASE_PATENT_RAW_BUCKET=patent-raw

# JPO API (optional)
JPO_API_BASE_URL=
JPO_API_KEY=
JPO_API_TIMEOUT_SECONDS=30

# Cron (Vercel)
CRON_SECRET=your-secret

# Safety (explicit approval required for schema changes)
ALLOW_SCHEMA_INIT=false

# Auth (API requires Supabase access token)
AUTH_ENABLED=true

# JP Index export controls (optional)
JP_INDEX_EXPORT_ENABLED=true
JP_INDEX_EXPORT_MAX=10000
JP_INDEX_EXPORT_TOKEN=your-export-token
# If JP_INDEX_EXPORT_TOKEN is set, include header: X-Export-Token

# JP Index rate limit / cache
JP_INDEX_RATE_LIMIT_PER_MINUTE=120
JP_INDEX_CACHE_TTL_SECONDS=60
JP_INDEX_CACHE_MAX_ENTRIES=1000
```

## マイグレーション

Supabase migrations が正（`supabase/migrations/`）。手順は `docs/phase2-master-data-ops.md` を参照。
Alembic は履歴保持のみで、今後は実行しない。

## ローカル実行

```bash
# API サーバー起動
python -m app.cli serve

# CLI コマンド
python -m app.cli ingest --path ./data/raw --storage both
python -m app.cli parse --all
python -m app.cli runs list
python -m app.cli jp-index-import --path ./data/jp_index.jsonl --run-type delta --update-date 2026-02-04

# Ingestion jobs (local_path hint required for now)
python -m app.cli ingest-job --numbers "JP1234567B2" --local-path ./data/raw/sample.xml
python -m app.cli ingest-run --job-id <job_id> --storage supabase
python -m app.cli auth-approve-user --email user@example.com --approved true
```

## API エンドポイント

### 特許データ
- `GET /healthz` - ヘルスチェック
- `GET /v1/patents/resolve?input=...` - 特許番号の正規化
- `GET /v1/patents/{patent_id}/claims` - 請求項一覧（raw/norm）
- `GET /v1/patents/{patent_id}/claims/{no}` - 請求項取得
- `GET /v1/patents/{patent_id}/spec` - 明細書（セクション）
- `GET /v1/patents/{patent_id}/versions` - 版一覧

### 取込
- `POST /v1/ingest` - 取込ジョブ作成
- `GET /v1/ingest/jobs/{job_id}` - 取込ジョブ状態
- `GET /v1/jobs/{job_id}` - 取込ジョブ状態（エイリアス）

### 侵害分析
- `POST /v1/analysis/start` - 分析開始
- `GET /v1/analysis/{job_id}` - ジョブステータス
- `GET /v1/analysis/{job_id}/results` - 結果取得

### JP Patent Index
- `GET /v1/jp-index/search` - JP Index 検索
- `GET /v1/jp-index/resolve?input=...` - 番号正規化
- `GET /v1/jp-index/patents/{case_id}` - ケース詳細
- `GET /v1/jp-index/changes?from_date=YYYY-MM-DD` - 差分一覧
- `POST /v1/jp-index/export` - エクスポート
- `GET /v1/jp-index/ingest/runs` - 取り込み履歴

### Cron (定期実行)
- `POST /api/cron/batch-analyze` - バッチ分析実行
- `POST /api/cron/poll-patents` - 特許ステータス監視

## Vercelデプロイ

### 1. Vercelプロジェクト設定

```bash
# Vercel CLIでデプロイ
vercel --prod
```

### 2. 環境変数をVercelに設定

Vercel Dashboard > Settings > Environment Variables:
- `DATABASE_URL`
- `DIRECT_URL`
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `LLM_PROVIDER`
- `CRON_SECRET`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `AUTH_ENABLED`

### 3. Vercel Cron

`vercel.json`で定義済み:
- バッチ分析: 6時間ごと
- 特許監視: 毎日9時

## GitHub Actionsでの実行

### 手動実行

1. GitHub > Actions > "Patent Analysis"
2. "Run workflow"をクリック
3. パラメータを入力:
   - `patent_id`: JP1234567B2
   - `pipeline`: C
   - `target_product`: (任意)

### スケジュール実行

6時間ごとに自動実行（pending状態のジョブを処理）

### シークレット設定

GitHub > Settings > Secrets and variables > Actions:
- `DATABASE_URL`
- `DIRECT_URL`
- `OPENAI_API_KEY`
- `LLM_PROVIDER`

## フロントエンド

```bash
cd frontend
npm install
npm run dev  # http://localhost:3002
```

## 開発

```bash
ruff check .      # Lint
ruff format .     # Format
mypy app          # Type check
pytest            # Test
```
