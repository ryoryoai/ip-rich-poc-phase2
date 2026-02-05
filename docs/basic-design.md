# 基本設計書

作成日: 2026-02-04  
対象システム: Phase 1 特許侵害調査システム（PoC）

## 1. システム構成
### 1.1 構成要素
- クライアント: Next.js App Router（React）
- サーバ/API: Next.js Route Handlers
- 認証: Supabase Auth（SSR Cookie）
- DB: Supabase Postgres + Prisma
- 外部連携: OpenAI Deep Research / OpenAI Chat Completion / J-PlatPat（Provider 経由）
- オプション: Tavily（検索プロバイダー）

### 1.2 論理構成（概要）
```
Browser
  -> Next.js UI
  -> Next.js API Routes
     -> Prisma -> Supabase Postgres
     -> OpenAI (Deep Research, Chat Completion)
     -> Providers (LLM/Search/Patent/Storage)
```

## 2. 主要フロー
### 2.1 DB保存版 調査フロー
1. `/research` で特許番号・請求項1を入力し `/api/analyze/start` を実行
2. `analysis_jobs` に `pending` で保存
3. `/api/cron/check-and-do` が `pending` を `researching` へ遷移し OpenAI Deep Research を開始
4. 完了後、Webhook または `/api/analyze/status` で `completed` に遷移
5. `runStructuredAnalysis` が構成要件・判定・レポート・引用を生成し正規化テーブルに保存
6. `/research/result/[job_id]` で結果表示

### 2.2 失敗/再実行
- 失敗時は `failed` に遷移し、`/api/analyze/retry/[job_id]` で再実行可能
- `retryCount` と `maxRetries` により自動再試行の上限を制御

### 2.3 シンプル調査フロー
1. `/simple` で特許IDを入力し `/api/analyze-simple` 実行
2. J-PlatPat 情報取得 → Deep Search → 結果表示
3. DB保存は行わない（画面から JSON ダウンロードのみ）

## 3. 画面設計（主要画面）
### 3.1 `/`（ホーム）
- システム概要・フェーズ情報・利用手順の説明
- CTA: 「侵害調査を開始」→ `/research`

### 3.2 `/auth`（認証）
- サインアップ/ログイン/ログアウト
- セッション情報の表示
- メール確認用 Mailpit リンク

### 3.3 `/research`（DB保存版 調査開始）
- 入力: 特許番号、請求項1（全文）
- バリデーション: 必須入力
- 実行: `/api/analyze/start`
- 遷移: 既存結果→`/research/result/[job_id]`、新規→`/research/status/[job_id]`

### 3.4 `/research/list`（ジョブ一覧）
- ステータス絞り込み
- 主要情報: 特許番号、請求項プレビュー、優先度、作成/開始/終了日時
- リンク: ステータス/結果画面へ遷移

### 3.5 `/research/status/[job_id]`（ステータス監視）
- ステータス表示（pending/researching/analyzing/completed/failed）
- 30秒間隔でポーリング
- 失敗時は再実行ボタン

### 3.6 `/research/result/[job_id]`（結果）
- Deep Research レポート（Markdown）
- 引用一覧
- トークン使用量 / 推定コスト
- Raw JSON の表示・コピー（`?raw=1` で開閉）

### 3.7 `/simple`（簡易分析）
- 特許ID入力
- 進行状況表示（ステップ表示）
- 結果表示と JSON ダウンロード

## 4. API設計（抜粋）
### 4.1 認証・保護
- 認証対象: すべてのページ/API（Webhook・Auth を除く）
- Webhook: 署名検証
- Cron: `X-Cron-Secret` 必須

### 4.2 API一覧
#### 調査ジョブ系
- `POST /api/analyze/start`
  - req: `patentNumber`, `claimText`, `companyName`, `productName`
  - res: `job_id`, `status`, `created_at`, `existing?`
- `GET /api/analyze/list`
  - query: `status?`, `limit?`, `offset?`
  - res: `jobs[]`, `total`, `limit`, `offset`
- `GET /api/analyze/status/{job_id}`
  - res: `job_id`, `status`, `progress`, `error_message?`
- `GET /api/analyze/result/{job_id}`
  - res: 結果一式（完了前は 400）
- `POST /api/analyze/retry/{job_id}`
  - res: `job_id`, `status`, `progress`

#### 調査/特許情報
- `POST /api/analyze-simple`
  - req: `patentId`
  - res: `claim1`, `detectedProducts`, `infringementAnalysis` など
- `POST /api/analyze-deep`
  - req: `patentNumber`, `mode?`
  - res: `potentialInfringers`, `deepSearchResult`, `tpmInfo` など
- `POST /api/analyze`
  - req: `patentNumber`, `claimText`, `companyName`, `productName`
  - res: `requirements`, `complianceResults`, `summary`（ローカル保存）
- `POST /api/patent`
  - req: `patentNumber`
  - res: 特許情報（Provider 依存）

#### スケジュール/バッチ
- `POST /api/patent-search/schedule`
  - req: `patentNumber`, `claimText`, `priority?`, `scheduledFor?`, `searchType?`
  - res: `job_id`, `scheduled_for`, `estimated_completion`, `message`
- `GET /api/patent-search/schedule`
  - res: 優先度別グルーピング + 統計
- `POST /api/cron/check-and-do`（`GET` 互換）
  - header: `X-Cron-Secret`
  - res: 実行統計（started/completed/failed など）

#### Webhook/ヘルス
- `POST /api/webhook/openai`
  - header: `webhook-id`, `webhook-timestamp`, `webhook-signature`
  - res: `status`
- `POST /api/webhook/research`
  - req: `job_id`, `status`, `results?`, `patent_info?`
  - res: `status`
- `GET /api/ngrok/health`
  - res: `status`, `service`, `endpoints` など
- `GET/POST /api/test-prisma`
  - Prisma 接続テスト / テストジョブ作成

## 5. データ設計（概要）
### 5.1 主テーブル
- `analysis_jobs`: 入力/進捗/結果/エラー/優先度/スケジュール
- `patent_cases`: 特許単位の情報
- `claims`: 請求項（claim_no=1 のみ利用）
- `claim_elements`: 構成要件
- `companies` / `products` / `product_versions`
- `evidence` / `product_facts`
- `analysis_runs` / `element_assessments` / `element_assessment_evidence`

### 5.2 状態遷移
```
pending -> researching -> analyzing -> completed
                    -> failed
```

## 6. 非同期/バッチ設計
- `cron/check-and-do` が `pending` を開始し、OpenAI Deep Research をバックグラウンド実行
- `MAX_CONCURRENT_JOBS` により並列数を制御
- `priority` と `scheduledFor` により実行順を制御
- OpenAI 完了時:
  - Webhook受信 or `status` ポーリングで `completed` に更新
  - `runStructuredAnalysis` を実行し正規化保存

## 7. 認証・認可設計
- Middleware で Supabase Auth を検証し未認証は `/auth` へリダイレクト
- `/api/webhook/*` は認証バイパス（署名検証）

## 8. エラーハンドリング
- 4xx: 入力不足、ジョブ未存在、未完了
- 5xx: 外部 API / DB 例外
- 画面側はユーザー向けメッセージと再試行を提供

## 9. 設定・環境変数（主要）
- `DATABASE_URL`, `DIRECT_URL`
- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `OPENAI_API_KEY`, `OPENAI_WEBHOOK_SECRET`
- `OPENAI_DEEP_RESEARCH_MODEL`, `MAX_CONCURRENT_JOBS`
- `CRON_SECRET_KEY`, `NEXT_PUBLIC_APP_URL`
- `LLM_PROVIDER`, `SEARCH_PROVIDER`, `PATENT_PROVIDER`, `STORAGE_PROVIDER`
- `MODEL_NAME`, `MAX_TOKENS`, `TEMPERATURE`
