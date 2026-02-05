# 要件定義書

作成日: 2026-02-04  
対象システム: Phase 1 特許侵害調査システム（PoC）

## 1. 目的・背景
- 特許の請求項に基づき、侵害可能性のある製品候補を自動で探索・整理する。
- Deep Research と LLM を組み合わせた調査プロセスを PoC として検証する。
- 調査結果の保存・再参照・可視化を行い、業務利用の妥当性を評価する。

## 2. 対象範囲
### 2.1 対象（スコープ内）
- Web UI による調査ジョブ作成・状態確認・結果閲覧
- Supabase Auth を利用した認証
- Deep Research API と LLM による調査・構造化分析
- 調査ジョブの永続化（Supabase Postgres）
- Cron/Webhook による非同期処理
- テスト・ヘルスチェック用 API

### 2.2 対象外（スコープ外）
- マルチテナント/権限ロール管理
- 外部顧客向けの課金・請求
- 監視基盤・通知基盤の本番運用
- 法的判断の最終確定

## 3. 利用者・権限
- 利用者: 認証済みユーザーのみ
- 権限: ロール分離はなし（単一権限）
- 認証方式: Supabase Auth（メール/パスワード）

## 4. 機能一覧（ソース参照）
### 4.1 ユーザー向け機能
- 認証（サインアップ/ログイン/ログアウト、セッション表示）
- 侵害調査ジョブ作成（DB保存版）
- 調査ジョブ一覧・ステータス絞り込み
- 調査ステータス監視（ポーリング、リトライ）
- 調査結果表示（レポート、引用、トークン/コスト表示、Raw JSON）
- シンプル調査（J-PlatPat→Deep Search、DB保存なし、JSONダウンロード）

### 4.2 運用・内部機能
- Deep Research API 実行（バックグラウンド）
- 構造化分析（請求項分解・充足性判定・レポート生成）
- Cron によるジョブ実行管理（優先度・並列数・リトライ）
- Webhook 受信（OpenAI 完了イベント）
- 特許情報取得 API
- スケジュール登録 API
- Prisma 接続テスト API
- ngrok ヘルスチェック API

## 5. 機能要件
### 5.1 認証
- 未認証ユーザーは `/auth` へリダイレクトする。
- 認証済みユーザーは全画面を利用可能。
- Webhook 受信は認証バイパスし、署名検証を行う。

### 5.2 調査ジョブ作成（DB保存版）
- 入力: 特許番号、請求項1、企業名、製品名（UI では自動補完前提で「調査中…」を送信）
- 既に完了済みの同一特許番号がある場合は既存結果へ遷移する。
- 新規ジョブは `pending` で保存する。

### 5.3 ジョブ状態管理
- ステータス: `pending` / `researching` / `analyzing` / `completed` / `failed`
- 状態監視は 30 秒間隔でポーリングする。
- 失敗ジョブは `retry` により `pending` へ戻せる。

### 5.4 調査結果表示
- Deep Research レポートを Markdown として表示する。
- 引用 URL を一覧表示する。
- トークン使用量と推定コストを表示する。
- Raw JSON を表示/コピーできる。

### 5.5 シンプル調査
- 特許IDのみで実行し、J-PlatPat 由来の請求項1を取得する。
- Deep Search 実行後、結果を画面に表示し JSON ダウンロードを可能にする。
- DB保存は行わない。

### 5.6 スケジュール実行
- 優先度・実行時刻・検索タイプを指定してジョブを登録できる。
- 優先度に応じて実行時刻の推定メッセージを返す。

## 6. 非機能要件
### 6.1 性能
- Deep Research はバックグラウンドで実行する。
- 同時実行数は `MAX_CONCURRENT_JOBS` で制御する（デフォルト 3）。
- ジョブ一覧は 60 秒間隔で更新する。

### 6.2 セキュリティ
- 認証: Supabase Auth
- Webhook: 署名検証（`OPENAI_WEBHOOK_SECRET`）
- Cron: `X-Cron-Secret` ヘッダー検証
- 環境変数の必須チェック（起動時）

### 6.3 信頼性
- OpenAI API 失敗時はジョブを `failed` に遷移する。
- 失敗時は `retryCount` と `maxRetries` を用いて再試行する。

### 6.4 運用性
- 主要処理はサーバーログに出力する（console logging）。
- Prisma で DB 接続確認用 API を提供する。

## 7. データ要件（概要）
- `analysis_jobs`: 調査ジョブの状態・入力・結果の保存
- `patent_cases` / `claims` / `claim_elements`: 特許・請求項・要件分解
- `companies` / `products` / `product_versions`: 企業・製品マスタ
- `evidence` / `product_facts`: 根拠情報
- `analysis_runs` / `element_assessments`: 分析履歴と充足性判定

## 8. 外部連携
- OpenAI（Deep Research / Chat Completion）
- Supabase（Postgres, Auth）
- J-PlatPat（特許情報取得: Provider 経由）
- Tavily（検索プロバイダーとして任意）

## 9. 環境・構成要件
- フロント/サーバ: Next.js App Router
- DB: Supabase Postgres + Prisma
- 主要環境変数（例）:
  - `DATABASE_URL`, `DIRECT_URL`
  - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `OPENAI_API_KEY`, `OPENAI_WEBHOOK_SECRET`
  - `CRON_SECRET_KEY`, `MAX_CONCURRENT_JOBS`
  - `OPENAI_DEEP_RESEARCH_MODEL`, `LLM_PROVIDER`, `SEARCH_PROVIDER`, `PATENT_PROVIDER`
