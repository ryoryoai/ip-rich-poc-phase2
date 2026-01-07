---
sidebar_position: 1
sidebar_label: Phase 1 開発詳細
---

# Phase 1: 侵害調査自動化 - 開発詳細

Vercelの300秒タイムアウト制限に対応するため、OpenAI Deep Research APIの非同期モード（`background: true`）とCronを活用したアーキテクチャを実装しました。

## 概要

**期間**: 2024年10月後半〜12月末
**目標**: 特許1件あたりの侵害可能性を自動判定するシステムを構築
**稼働**: エンジニア0.1稼働

| 項目               | 実装内容                              |
| ------------------ | ------------------------------------- |
| **Deep Research**  | OpenAI API直接呼び出し（background: true） |
| **タイムアウト**   | 非同期処理により制限回避              |
| **データベース**   | Supabase PostgreSQL（Prisma経由）     |
| **ステータス管理** | Cron + Webhook + ポーリング           |
| **バッチ処理**     | Vercel Cron（15分ごと）               |

:::tip Vercelタイムアウト対策
OpenAI Deep Research APIの`background: true`オプションを使用することで、Vercelの300秒制限を回避。処理完了はWebhookで通知されます。
:::

---

## アーキテクチャ

### 現在のアーキテクチャ

![Phase 1 アーキテクチャ](./diagrams/phase1-architecture.svg)

:::info PlantUMLソースファイル
この図のPlantUMLソースは [diagrams/phase1-architecture.puml](./diagrams/phase1-architecture.puml) で管理されています。
:::

### システム構成図

```
┌─────────────┐
│   ユーザー   │
└──────┬──────┘
       │ 1. 分析リクエスト
       ▼
┌─────────────────────────┐
│   Next.js (Vercel)      │
│   /api/analyze/start    │
└──────┬──────────────────┘
       │ 2. ジョブ作成 (status: pending)
       │    ※OpenAI APIは呼び出さない
       ▼
┌─────────────────────────┐         ┌──────────────────┐
│   Next.js API Routes    │◄────────┤  Supabase        │
│   (Vercel)              │         │  PostgreSQL      │
│                         │         │  + Prisma ORM    │
│ - /api/analyze/start    │         └──────────────────┘
│ - /api/analyze/status   │
│ - /api/analyze/result   │
│ - /api/analyze/list     │
│ - /api/cron/check-and-do│
│ - /api/webhook/openai   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Cron Job               │◄─── Vercel Cron (15分ごと)
│  /api/cron/check-and-do │
│                         │
│  - pendingジョブ取得    │
│  - OpenAI API呼び出し   │
│  - researchingの確認    │
│  - リトライ処理         │
└──────┬──────────────────┘
       │ 3. OpenAI Deep Research開始
       │    (background: true)
       ▼
┌─────────────────────────┐
│  OpenAI Deep Research   │
│  (background: true)     │
│                         │
│  - o4-mini-deep-research│
│  - 5-15分で実行         │
└──────┬──────────────────┘
       │ 4. 完了通知
       ▼
┌─────────────────────────┐
│  結果受信               │
│  - Webhook: /api/webhook/openai
│  - Polling: Cronで定期確認
│  → status: completed    │
└─────────────────────────┘
```

### 処理フロー

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant N as Next.js API
    participant DB as PostgreSQL
    participant C as Cron Job
    participant O as OpenAI API

    U->>N: POST /api/analyze/start
    N->>DB: ジョブ作成 (status: pending)
    N-->>U: job_id, status: pending

    Note over C: 15分ごとにCron実行
    C->>N: POST /api/cron/check-and-do
    N->>DB: pendingジョブ取得
    N->>O: Deep Research (background: true)
    O-->>N: response.id
    N->>DB: status: researching

    Note over O: Deep Research実行中...

    alt Webhook経由
        O->>N: POST /api/webhook/openai
        N->>DB: 結果保存 (completed)
    else Polling経由
        C->>N: POST /api/cron/check-and-do
        N->>O: responses.retrieve(id)
        O-->>N: status: completed, output
        N->>DB: 結果保存 (completed)
    end

    U->>N: GET /api/analyze/status/:id
    N->>DB: ステータス取得
    N-->>U: status: completed

    U->>N: GET /api/analyze/result/:id
    N->>DB: 結果取得
    N-->>U: 分析結果
```

---

## プロジェクト構造

```
ip-rich-tools/
├── infra/                           # Terraform インフラ
├── docs-site/                       # Docusaurus ドキュメント
└── apps/
    └── poc/
        └── phase1/                  # Phase 1: 侵害調査自動化（Next.js）
            ├── README.md
            ├── package.json
            ├── tsconfig.json
            ├── next.config.js
            ├── tailwind.config.ts
            ├── .env.local.example
            ├── prisma/
            │   └── schema.prisma    # データベーススキーマ
            ├── src/
            │   ├── app/             # Next.js App Router
            │   │   ├── layout.tsx
            │   │   ├── page.tsx     # トップページ（Phase状態表示）
            │   │   ├── research/    # 分析UI（メイン）
            │   │   │   ├── page.tsx
            │   │   │   ├── list/page.tsx
            │   │   │   ├── status/[job_id]/page.tsx
            │   │   │   └── result/[job_id]/page.tsx
            │   │   └── api/
            │   │       ├── analyze/
            │   │       │   ├── start/route.ts
            │   │       │   ├── status/[job_id]/route.ts
            │   │       │   ├── result/[job_id]/route.ts
            │   │       │   ├── list/route.ts
            │   │       │   └── retry/[job_id]/route.ts
            │   │       ├── patent-search/
            │   │       │   └── schedule/route.ts
            │   │       ├── cron/
            │   │       │   └── check-and-do/route.ts
            │   │       └── webhook/
            │   │           └── openai/route.ts
            │   ├── components/
            │   │   └── ui/          # shadcn/ui
            │   ├── lib/
            │   │   ├── prisma.ts    # Prismaクライアント
            │   │   └── container.ts # DIコンテナ
            │   ├── services/        # コアビジネスロジック
            │   └── interfaces/      # プロバイダーインターフェース
            └── public/
```

---

## データベース設計

### Prisma + Supabase PostgreSQL

Supabaseの無料プランを使用し、Prismaで型安全なデータベースアクセスを実現。

#### スキーマ

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")
}

model analysis_jobs {
  id        String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  createdAt DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
  updatedAt DateTime @default(now()) @updatedAt @map("updated_at") @db.Timestamptz(6)

  // ジョブステータス
  status       String  @db.Text  // pending, researching, analyzing, completed, failed
  progress     Int     @default(0) @db.Integer
  errorMessage String? @map("error_message") @db.Text

  // 入力データ
  patentNumber String @map("patent_number") @db.Text
  claimText    String @map("claim_text") @db.Text
  companyName  String @map("company_name") @db.Text
  productName  String @map("product_name") @db.Text

  // Deep Research結果
  openaiResponseId String? @map("openai_response_id") @db.Text
  inputPrompt      String? @map("input_prompt") @db.Text
  researchResults  Json?   @map("research_results") @db.JsonB

  // 分析結果（拡張用）
  requirements      Json? @db.JsonB
  complianceResults Json? @map("compliance_results") @db.JsonB
  summary           Json? @db.JsonB

  // バッチ処理用
  priority      Int       @default(5)
  scheduledFor  DateTime? @map("scheduled_for") @db.Timestamptz(6)
  retryCount    Int       @default(0) @map("retry_count")
  maxRetries    Int       @default(3) @map("max_retries")
  batchId       String?   @map("batch_id") @db.Text
  searchType    String    @default("infringement_check") @map("search_type") @db.Text

  // 追加の分析結果（拡張用）
  infringementScore Float? @map("infringement_score")
  revenueEstimate   Json?  @map("revenue_estimate") @db.JsonB

  // タイムスタンプ
  queuedAt    DateTime? @map("queued_at") @db.Timestamptz(6)
  startedAt   DateTime? @map("started_at") @db.Timestamptz(6)
  finishedAt  DateTime? @map("finished_at") @db.Timestamptz(6)

  // メタデータ（拡張用）
  userId    String? @map("user_id") @db.Uuid
  ipAddress String? @map("ip_address") @db.Text

  @@index([status], map: "idx_jobs_status")
  @@index([createdAt(sort: Desc)], map: "idx_jobs_created_at")
  @@index([userId], map: "idx_jobs_user_id")
  @@index([status, priority, scheduledFor], map: "idx_jobs_queue")
  @@index([batchId], map: "idx_jobs_batch")
}
```

---

## APIエンドポイント

### 1. `POST /api/analyze/start` - 分析開始

企業名・製品名を指定して分析ジョブを作成します。

**リクエスト**:
```typescript
interface AnalyzeStartRequest {
  patentNumber: string;
  claimText: string;
  companyName: string;
  productName: string;
}
```

**レスポンス**:
```typescript
interface AnalyzeStartResponse {
  job_id: string;
  status: 'pending' | 'completed';
  created_at: string;
  existing?: boolean;  // 既存の完了ジョブがある場合
}
```

### 2. `POST /api/cron/check-and-do` - Cronジョブハンドラー

Vercel Cronから15分ごとに呼び出されます。

**ヘッダー**:
```
X-Cron-Secret: {CRON_SECRET_KEY}
```

**処理内容**:
1. 実行中ジョブ（status='researching'）のOpenAI APIステータス確認
2. 完了したジョブの結果を保存
3. 新規pendingジョブをDeep Researchに投入（最大同時実行数まで）

**レスポンス**:
```typescript
interface CronResponse {
  checked: number;
  completed: number;
  failed: number;
  started: number;
  currentRunning: number;
  stats: Record<string, number>;
}
```

### 3. `POST /api/webhook/openai` - OpenAI Webhook

OpenAI Deep Research完了時に呼び出されるWebhook。

**セキュリティ**:
- Basic認証はバイパス（middleware.tsで設定）
- OpenAI Webhook署名検証を実施

### 4. `GET /api/analyze/status/[job_id]` - ステータス確認

**レスポンス**:
```typescript
interface AnalyzeStatusResponse {
  job_id: string;
  status: 'pending' | 'researching' | 'analyzing' | 'completed' | 'failed';
  progress: number;  // 0-100
  error_message?: string;
}
```

:::info ステータスAPIの自動保存機能
ステータス確認時にOpenAI APIにポーリングし、完了していれば自動的に結果を保存します。
これにより、Webhookが失敗した場合でもフロントエンドからのポーリングで結果を取得できます。
:::

### 5. `GET /api/analyze/result/[job_id]` - 結果取得

### 6. `GET /api/analyze/list` - ジョブ一覧

### 7. `POST /api/analyze/retry/[job_id]` - リトライ

失敗したジョブをpendingに戻してリトライ。

---

## OpenAI Deep Research API

### 呼び出し方法

```typescript
const response = await openai.responses.create({
  model: 'o4-mini-deep-research-2025-06-26',
  input: [
    {
      type: 'message',
      role: 'user',
      content: query,
    },
  ],
  reasoning: { summary: 'auto' },
  tools: [{ type: 'web_search_preview' }],
  background: true,  // 非同期モード
  metadata: { job_id: job.id },
});
```

### Webhook設定

OpenAI Dashboard (https://platform.openai.com/webhooks) で設定:

1. **URL**: `https://ip-rich-poc-phase1.vercel.app/api/webhook/openai`
2. **Events**: `response.completed`
3. **Signing Secret**: 環境変数 `OPENAI_WEBHOOK_SECRET` に設定

---

## Cron設定

### Vercel Cron

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/check-and-do",
      "schedule": "*/15 * * * *"
    }
  ]
}
```

:::tip Vercel Cron
Proプランで15分間隔に対応。設定がシンプルで管理が容易です。
:::

---

## フロントエンド実装

### ページ構成

```
apps/poc/phase1/src/app/research/
├── page.tsx                    # 新規分析フォーム
├── list/page.tsx               # 分析履歴一覧
├── status/[job_id]/page.tsx    # ステータス確認（ポーリング）
└── result/[job_id]/page.tsx    # 結果表示
```

### ポーリング仕様

- **ステータスページ**: 30秒間隔、最大15分（30回）でタイムアウト
- **一覧ページ**: 1分間隔で自動更新（React Query使用）

---

## 環境変数設定

### Vercel環境変数

```bash
# ===== データベース（Prisma） =====
DATABASE_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:6543/postgres?schema=production&pgbouncer=true
DIRECT_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:5432/postgres?schema=production

# ===== LLMプロバイダー =====
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_DEEP_RESEARCH_MODEL=o4-mini-deep-research-2025-06-26

# ===== 検索プロバイダー =====
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-xxxxx

# ===== OpenAI Webhook =====
OPENAI_WEBHOOK_SECRET=whsec_xxxxx
OPENAI_WEBHOOK_URL=https://ip-rich-poc-phase1.vercel.app/api/webhook/openai

# ===== Cron設定 =====
CRON_SECRET_KEY=your-secure-random-string
MAX_CONCURRENT_JOBS=3

# ===== Basic認証 =====
BASIC_AUTH_USERNAME=patent
BASIC_AUTH_PASSWORD=xxxxx
SKIP_AUTH=false

# ===== Next.js =====
NEXT_PUBLIC_APP_URL=https://ip-rich-poc-phase1.vercel.app
```

:::tip プロバイダー切り替え
`LLM_PROVIDER` と `SEARCH_PROVIDER` を変更することで、バックエンドの実装を変更せずにプロバイダーを切り替えられます。
:::

---

## コスト試算

```
Supabase無料枠:
  - データベース: 500MB（無料）
  - API呼び出し: 制限なし

OpenAI Deep Research:
  - 使用量に応じた従量課金
  - 1件あたり約$0.10〜$0.50（検索量による）

Vercel:
  - Pro: $20/月（15分Cronに必要）

月額コスト目安:
  - 開発中: $20〜$25
  - 本番運用: $20〜$50
```

---

## 実装完了チェックリスト

- [x] Supabase PostgreSQL + Prisma設定
- [x] Next.js APIルート実装
  - [x] /api/analyze/start（ジョブ作成）
  - [x] /api/analyze/status/[job_id]（ステータス確認 + 自動保存）
  - [x] /api/analyze/result/[job_id]（結果取得）
  - [x] /api/analyze/list（一覧取得）
  - [x] /api/analyze/retry/[job_id]（失敗ジョブのリトライ）
  - [x] /api/cron/check-and-do（バッチ処理）
  - [x] /api/webhook/openai（Webhook受信）
- [x] OpenAI Deep Research API統合
- [x] Webhook署名検証
- [x] Vercel Cron設定
- [x] フロントエンド実装
  - [x] 新規分析フォーム（/research）
  - [x] 一覧ページ（/research/list）
  - [x] ステータスページ（/research/status/[job_id]）
  - [x] 結果ページ（/research/result/[job_id]）
  - [x] リトライ機能
- [x] 環境変数設定（Vercel）
- [x] プロバイダー切り替え機能（LLM/Search）
- [x] 本番デプロイ

---

## 今後の拡張案

### Phase 2: 業務利用可能性検証

- 侵害調査結果の妥当性確認
- 特許有識者によるレビュー

### Phase 3: 機能拡張

- J-PlatPat連携による特許情報自動取得
- 侵害調査結果の管理・検索機能
- 侵害額推定機能
- CSV出力機能

### Phase 4: 商用化対応

- ログイン機能
- ユーザー・グループ管理
- 利用料管理

---

:::tip アーキテクチャのメリット

- ✅ Vercelタイムアウト制限を回避（非同期処理）
- ✅ OpenAI Deep Research API直接利用（別サービス不要）
- ✅ Vercel Cronで定期実行
- ✅ Webhookで確実に結果を受信
- ✅ Polling（フォールバック）で信頼性向上
- ✅ Prismaによる型安全なDB操作
:::
