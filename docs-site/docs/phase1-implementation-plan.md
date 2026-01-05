---
sidebar_position: 5
---

# Phase 1: 侵害調査自動化 - 実装計画

Phase 1（侵害調査の自動化）の詳細な実装計画と現在の実装状況です。

## 概要

**期間**: 2024年10月後半〜12月末
**目標**: 特許1件あたりの侵害可能性を自動判定するシステムを構築
**稼働**: エンジニア0.1稼働

## 現在のアーキテクチャ

![Phase 1 アーキテクチャ](./diagrams/phase1-architecture.svg)

:::info PlantUMLソースファイル
この図のPlantUMLソースは [diagrams/phase1-architecture.puml](./diagrams/phase1-architecture.puml) で管理されています。
:::

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
            │   │   ├── analyze/
            │   │   │   └── page.tsx # 分析UI
            │   │   └── api/
            │   │       ├── analyze/
            │   │       │   ├── start/route.ts    # 分析開始
            │   │       │   ├── status/[job_id]/route.ts
            │   │       │   ├── result/[job_id]/route.ts
            │   │       │   └── list/route.ts
            │   │       ├── patent-search/
            │   │       │   └── schedule/route.ts # バッチスケジュール
            │   │       ├── cron/
            │   │       │   └── check-and-do/route.ts  # Cronハンドラー
            │   │       └── webhook/
            │   │           └── openai/route.ts   # OpenAI Webhook
            │   ├── components/
            │   │   └── ui/          # shadcn/ui
            │   ├── lib/
            │   │   └── prisma.ts    # Prismaクライアント
            │   ├── services/        # コアビジネスロジック
            │   │   ├── PatentInfringementAnalyzer.ts
            │   │   ├── RequirementExtractionService.ts
            │   │   └── ComplianceCheckService.ts
            │   └── interfaces/      # プロバイダーインターフェース
            └── public/
                └── current-workflow.svg
```

---

## APIエンドポイント

### 1. `POST /api/analyze/start` - 分析開始（即座実行）

企業名・製品名を指定して即座に分析を開始します。

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

**処理フロー**:
1. リクエストバリデーション
2. 同じ特許番号の完了済みジョブをチェック（あれば返却）
3. Prismaでジョブ作成（status: 'pending'）
4. OpenAI Deep Research API呼び出し（`background: true`）
5. ジョブを'researching'に更新、response.idを保存

### 2. `POST /api/patent-search/schedule` - バッチスケジュール

優先度を指定してジョブをスケジュールします（企業名・製品名は自動検出）。

**リクエスト**:
```typescript
interface PatentSearchScheduleRequest {
  patentNumber: string;
  claimText: string;
  priority?: number;           // 0-10（デフォルト: 5）
  scheduledFor?: string;       // ISO8601形式
  searchType?: 'infringement_check' | 'revenue_estimation' | 'comprehensive';
}
```

**レスポンス**:
```typescript
interface PatentSearchScheduleResponse {
  job_id: string;
  status: 'scheduled';
  priority: number;
  scheduled_for?: string;
  estimated_completion: string;
  message: string;
}
```

**優先度による実行時刻**:
- **9以上**: 即座に実行
- **8**: 22:00 JST
- **4-7**: 23:00 JST
- **0-3**: 00:00 JST

### 3. `POST /api/cron/check-and-do` - Cronジョブハンドラー

GitHub Actionsから15分ごとに呼び出されます。

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

### 4. `POST /api/webhook/openai` - OpenAI Webhook

OpenAI Deep Research完了時に呼び出されるWebhook。

**セキュリティ**:
- Basic認証はバイパス（middleware.tsで設定）
- OpenAI Webhook署名検証を実施

**処理内容**:
1. `webhook-signature`ヘッダーを検証
2. `response.completed`イベントを処理
3. `openaiResponseId`でジョブを検索
4. 検索結果をPrismaに保存

### 5. `GET /api/analyze/status/[job_id]` - ステータス確認

**レスポンス**:
```typescript
interface AnalyzeStatusResponse {
  job_id: string;
  status: 'pending' | 'researching' | 'analyzing' | 'completed' | 'failed';
  progress: number;  // 0-100
  error_message?: string;
}
```

### 6. `GET /api/analyze/result/[job_id]` - 結果取得

**レスポンス**:
```typescript
interface AnalyzeResultResponse {
  job_id: string;
  status: 'completed';
  created_at: string;
  updated_at: string;
  patent_number: string;
  company_name: string;
  product_name: string;
  claim_text: string;
  input_prompt: string;
  research_results: {
    reportText: string;
    citations: Array<{
      type: string;
      title: string;
      url: string;
    }>;
    rawResponse: any;
    usage: any;
  };
  requirements?: any;
  compliance_results?: any;
  summary?: any;
}
```

### 7. `GET /api/analyze/list` - ジョブ一覧

**クエリパラメータ**:
- `limit`: 取得件数（デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）
- `status`: フィルタリング

---

## データベーススキーマ（Prisma）

```prisma
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

  // 分析結果
  requirements      Json? @db.JsonB
  complianceResults Json? @map("compliance_results") @db.JsonB
  summary           Json? @db.JsonB

  // バッチ処理用フィールド
  priority      Int       @default(5)
  scheduledFor  DateTime? @map("scheduled_for") @db.Timestamptz(6)
  retryCount    Int       @default(0) @map("retry_count")
  maxRetries    Int       @default(3) @map("max_retries")
  batchId       String?   @map("batch_id") @db.Text
  searchType    String    @default("infringement_check") @map("search_type") @db.Text

  // 追加フィールド
  infringementScore Float? @map("infringement_score")
  revenueEstimate   Json?  @map("revenue_estimate") @db.JsonB

  // タイムスタンプ
  queuedAt    DateTime? @map("queued_at") @db.Timestamptz(6)
  startedAt   DateTime? @map("started_at") @db.Timestamptz(6)
  finishedAt  DateTime? @map("finished_at") @db.Timestamptz(6)

  // メタデータ
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

## GitHub Actions Cron設定

```yaml
# .github/workflows/cron-patent-search.yml
name: Patent Search Batch Processing

on:
  schedule:
    - cron: '*/15 * * * *'  # 15分ごと
  workflow_dispatch:        # 手動実行用

jobs:
  batch-process:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Trigger cron endpoint
        run: |
          curl -X GET \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET_KEY }}" \
            -u "${{ secrets.BASIC_AUTH_USERNAME }}:${{ secrets.BASIC_AUTH_PASSWORD }}" \
            https://ip-rich-poc-phase1.vercel.app/api/cron/check-and-do
```

---

## 環境変数

```bash
# .env.local

# データベース（Prisma）
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?schema=production&pgbouncer=true
DIRECT_URL=postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?schema=production

# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_DEEP_RESEARCH_MODEL=o4-mini-deep-research-2025-06-26

# OpenAI Webhook
OPENAI_WEBHOOK_SECRET=whsec_xxxxx
OPENAI_WEBHOOK_URL=https://ip-rich-poc-phase1.vercel.app/api/webhook/openai

# Cron設定
CRON_SECRET_KEY=your-secure-random-string
MAX_CONCURRENT_JOBS=3

# Basic認証
BASIC_AUTH_USERNAME=patent
BASIC_AUTH_PASSWORD=xxxxx
SKIP_AUTH=false

# Next.js
NEXT_PUBLIC_APP_URL=https://ip-rich-poc-phase1.vercel.app
```

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
  background: true,  // 非同期モード（Webhookで結果を受信）
  metadata: { job_id: job.id },
});
```

### Webhookの設定

OpenAI Dashboard (https://platform.openai.com/webhooks) で設定:
- URL: `https://ip-rich-poc-phase1.vercel.app/api/webhook/openai`
- イベント: `response.completed`

---

## 侵害調査プロンプト

```
下記の特許{特許番号}の請求項１の要件を満たす侵害製品を念入りに調査せよ。
対象は日本国内でサービス展開している外国企業（日本企業以外）とする。

▼重要指示：
・**実際に侵害可能性が高い製品を優先的に探すこと**
・以下の分野の企業を重点的に調査すること：
  1. スポーツテック企業（モーションキャプチャ、動作解析システム）
  2. スポーツトレーニング・分析システム企業
  3. VR/ARスポーツトレーニング企業
  4. AIを使ったスポーツコーチング企業
  5. 球技のパフォーマンス解析システム企業

▼要求事項：
・請求項１に記載された**すべての構成要件を満たす製品のみ**を調査対象とする
・特許番号と請求項１の全文を**完全に照合**の上で処理すること
・請求項１の構成要件をそのまま引用して記載する
・各構成要件ごとに、製品の仕様と比較し、充足性（○/×）を判断
・**web検索を使用して**、製品の公開仕様・企業ページ・販売情報などを確認
・**侵害可能性がある製品を最低1つは見つけるよう努力**し、3社以上について判定

▼出力フォーマット（企業ごとにテーブルを作成）：

## 企業名1（例：Catapult Sports - 製品名：Vector等）
| 構成要件 | 製品の対応構成 | 充足判断 | 根拠 |
|----------|--------------|---------|------|
| 構成要件A（請求項1から引用） | 製品での具体的な実装内容 | ○/× | URL・公開情報等 |

**総合判定**: ○/× （全構成要件を満たす場合のみ○）

＜以下、特許{特許番号}（請求項１を全文で記載）＞
{請求項1}
```

---

## 達成した機能（Phase 1）

- ✅ 侵害調査の自動実行（OpenAI Deep Research API）
- ✅ バッチ処理による夜間実行（GitHub Actions Cron）
- ✅ 侵害調査履歴の閲覧（ジョブ一覧・詳細表示）
- ✅ 優先度に基づくスケジューリング
- ✅ Webhook による非同期結果受信

---

## 次のステップ（Phase 2以降）

### Phase 2: 業務利用可能性検証

- 侵害調査結果の妥当性確認
- 特許有識者によるレビュー

### Phase 3: 機能拡張

- J-PlatPat連携
- 侵害調査結果の管理・検索
- 侵害額推定
- CSV出力

---

## 関連資料

- [PoC開発計画 v1.1](./poc-development-plan-v1.1.md) - 非同期処理アーキテクチャ
- [特許侵害調査ワークフロー](./patent-workflow.md) - 自動化対象のワークフロー
