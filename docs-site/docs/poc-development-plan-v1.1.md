---
sidebar_position: 5
---

# PoC開発計画 v1.1（実装完了版）

Vercelの300秒タイムアウト制限に対応するため、OpenAI Deep Research APIの非同期モード（`background: true`）とGitHub Actions Cronを活用したアーキテクチャを実装しました。

## 📋 概要

| 項目               | 実装内容                              |
| ------------------ | ------------------------------------- |
| **Deep Research**  | OpenAI API直接呼び出し（background: true） |
| **タイムアウト**   | 非同期処理により制限回避              |
| **データベース**   | Supabase PostgreSQL（Prisma経由）     |
| **ステータス管理** | Cron + Webhook + ポーリング           |
| **バッチ処理**     | GitHub Actions（15分ごと）            |

:::tip Vercelタイムアウト対策
OpenAI Deep Research APIの`background: true`オプションを使用することで、Vercelの300秒制限を回避。処理完了はWebhookで通知されます。
:::

---

## 🏗️ アーキテクチャ

### システム構成図（現在の実装）

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
│  Cron Job               │◄─── GitHub Actions (15分ごと)
│  /api/cron/check-and-do │      または Vercel Cron
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

### 処理フロー（実際の実装）

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

## 🗄️ データベース設計

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
  status       String  @db.Text
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
  requirements      Json? @db.JsonB                        // 構成要件
  complianceResults Json? @map("compliance_results") @db.JsonB  // コンプライアンス結果
  summary           Json? @db.JsonB                        // サマリー

  // バッチ処理用
  priority      Int       @default(5)                                   // 優先度 (0-10)
  scheduledFor  DateTime? @map("scheduled_for") @db.Timestamptz(6)     // 実行予定時刻
  retryCount    Int       @default(0) @map("retry_count")              // リトライ回数
  maxRetries    Int       @default(3) @map("max_retries")              // 最大リトライ数
  batchId       String?   @map("batch_id") @db.Text                    // バッチID
  searchType    String    @default("infringement_check") @map("search_type") @db.Text

  // 追加の分析結果（拡張用）
  infringementScore Float? @map("infringement_score")      // 侵害可能性スコア (0-100)
  revenueEstimate   Json?  @map("revenue_estimate") @db.JsonB  // 売上推定

  // タイムスタンプ
  queuedAt    DateTime? @map("queued_at") @db.Timestamptz(6)   // キュー追加時刻
  startedAt   DateTime? @map("started_at") @db.Timestamptz(6)  // 処理開始時刻
  finishedAt  DateTime? @map("finished_at") @db.Timestamptz(6) // 処理完了時刻

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

### ローカル開発環境

#### Supabase CLI使用

```bash
# Supabase CLIインストール
npm install -g supabase

# ローカルSupabaseインスタンス起動
supabase init
supabase start

# Prismaスキーマをプッシュ
npx prisma db push

# ローカルURL: http://localhost:54321
# PostgreSQL: postgresql://postgres:postgres@localhost:54322/postgres?schema=local
```

---

## 🔄 OpenAI Deep Research API

### ジョブ作成（/api/analyze/start）

```typescript
// apps/poc/phase1/src/app/api/analyze/start/route.ts
export async function POST(request: NextRequest) {
  const { patentNumber, claimText, companyName, productName } = await request.json();

  // プロンプトを生成（cronジョブで使用するため事前に保存）
  const query = buildInfringementPrompt(patentNumber, claimText);

  // ジョブ作成（Prisma使用）- pendingで作成
  const job = await prisma.analysis_jobs.create({
    data: {
      status: "pending",  // pendingで作成
      patentNumber,
      claimText,
      companyName,
      productName,
      inputPrompt: query,  // プロンプトを保存
      progress: 0,
    },
  });

  // 注: OpenAI APIの呼び出しはcronジョブで実行される
  // /api/cron/check-and-do が定期的にpendingジョブを処理

  return NextResponse.json({
    job_id: job.id,
    status: "pending",
    created_at: job.createdAt.toISOString(),
  });
}
```

### Cronジョブ処理（/api/cron/check-and-do）

```typescript
// apps/poc/phase1/src/app/api/cron/check-and-do/route.ts
export async function POST(request: NextRequest) {
  // 1. 実行中ジョブのステータス確認（Polling）
  const inProgressJobs = await prisma.analysis_jobs.findMany({
    where: { status: 'researching' },
  });

  for (const job of inProgressJobs) {
    const response = await openai.responses.retrieve(job.openaiResponseId);
    if (response.status === 'completed') {
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: {
          status: 'completed',
          researchResults: response.output,
          finishedAt: new Date(),
        },
      });
    }
  }

  // 2. 新規ジョブの開始
  const pendingJobs = await prisma.analysis_jobs.findMany({
    where: { status: 'pending' },
    orderBy: [{ priority: 'desc' }, { createdAt: 'asc' }],
    take: maxConcurrent - currentRunning,
  });

  for (const job of pendingJobs) {
    // 保存済みのプロンプトを使用
    const query = job.inputPrompt || buildInfringementQuery(job.patentNumber, job.claimText);

    // OpenAI Deep Research API呼び出し
    const response = await openai.responses.create({
      model: 'o4-mini-deep-research-2025-06-26',
      input: [{ type: 'message', role: 'user', content: query }],
      reasoning: { summary: 'auto' },
      tools: [{ type: 'web_search_preview' }],
      background: true,  // 非同期モード
      metadata: { job_id: job.id },
    });

    await prisma.analysis_jobs.update({
      where: { id: job.id },
      data: {
        status: 'researching',
        openaiResponseId: response.id,
        startedAt: new Date(),
      },
    });
  }
}
```

### ステータス確認（/api/analyze/status/[job_id]）

```typescript
// apps/poc/phase1/src/app/api/analyze/status/[job_id]/route.ts
export async function GET(request: NextRequest, { params }) {
  const job = await prisma.analysis_jobs.findUnique({
    where: { id: params.job_id },
  });

  // researching状態でOpenAI APIに直接問い合わせ
  if (job.status === 'researching' && job.openaiResponseId) {
    const openaiResponse = await openai.responses.retrieve(job.openaiResponseId);

    // 完了していたら結果を保存
    if (openaiResponse.status === 'completed') {
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: {
          status: 'completed',
          progress: 100,
          researchResults: parseResponse(openaiResponse),
        },
      });
    }
  }

  return NextResponse.json({
    job_id: job.id,
    status: job.status,
    progress: job.progress,
    error_message: job.errorMessage,
  });
}
```

:::info ステータスAPIの自動保存機能
ステータス確認時にOpenAI APIにポーリングし、完了していれば自動的に結果を保存します。
これにより、Webhookが失敗した場合でもフロントエンドからのポーリングで結果を取得できます。
:::

### 失敗ジョブのリトライ（/api/analyze/retry/[job_id]）

```typescript
// apps/poc/phase1/src/app/api/analyze/retry/[job_id]/route.ts
export async function POST(request: NextRequest, { params }) {
  const job = await prisma.analysis_jobs.findUnique({
    where: { id: params.job_id },
  });

  // failedステータスのジョブのみリトライ可能
  if (job.status !== 'failed') {
    return NextResponse.json(
      { error: `Cannot retry job with status: ${job.status}` },
      { status: 400 }
    );
  }

  // ジョブをpendingに戻す
  const updatedJob = await prisma.analysis_jobs.update({
    where: { id: params.job_id },
    data: {
      status: 'pending',
      progress: 0,
      errorMessage: null,
      retryCount: job.retryCount + 1,
      openaiResponseId: null,
      researchResults: null,
    },
  });

  return NextResponse.json({
    job_id: updatedJob.id,
    status: updatedJob.status,
  });
}
```

### Webhook受信（/api/webhook/openai）

```typescript
// apps/poc/phase1/src/app/api/webhook/openai/route.ts
export async function POST(request: NextRequest) {
  // 1. 署名検証
  const wh = new Webhook(process.env.OPENAI_WEBHOOK_SECRET!);
  wh.verify(payload, headers);

  // 2. イベント処理
  const event = JSON.parse(payload);
  if (event.type === 'response.completed') {
    const { id: responseId, output } = event.data;

    // 3. ジョブ検索
    const job = await prisma.analysis_jobs.findFirst({
      where: { openaiResponseId: responseId },
    });

    // 4. 結果保存
    await prisma.analysis_jobs.update({
      where: { id: job.id },
      data: {
        status: 'completed',
        progress: 100,
        researchResults: { reportText, citations, rawResponse },
      },
    });
  }
}
```

### Webhook設定

OpenAI Dashboard (https://platform.openai.com/webhooks) で設定:

1. **URL**: `https://ip-rich-poc-phase1.vercel.app/api/webhook/openai`
2. **Events**: `response.completed`
3. **Signing Secret**: 環境変数 `OPENAI_WEBHOOK_SECRET` に設定

---

## ⏰ GitHub Actions Cron

### ワークフロー設定

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
          curl -s -w "\n%{http_code}" -X GET \
            -H "X-Cron-Secret: ${{ secrets.CRON_SECRET_KEY }}" \
            -u "${{ secrets.BASIC_AUTH_USERNAME }}:${{ secrets.BASIC_AUTH_PASSWORD }}" \
            https://ip-rich-poc-phase1.vercel.app/api/cron/check-and-do
```

### Vercel Cron設定

```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "regions": ["hnd1"],
  "functions": {
    "app/api/analyze/start/route.ts": {
      "maxDuration": 30
    },
    "app/api/analyze/status/[id]/route.ts": {
      "maxDuration": 10
    },
    "app/api/webhook/openai/route.ts": {
      "maxDuration": 30
    },
    "app/api/cron/check-and-do/route.ts": {
      "maxDuration": 60
    }
  },
  "crons": [
    {
      "path": "/api/cron/check-and-do",
      "schedule": "*/15 * * * *"
    }
  ],
  "env": {
    "NODE_ENV": "production"
  }
}
```

:::tip Vercel Cron vs GitHub Actions
- **Vercel Cron（推奨）**: Proプランで15分間隔対応。設定がシンプル。
- **GitHub Actions**: 無料プランでも利用可能。より詳細な制御が可能。
:::

---

## 🎨 フロントエンド実装

### ページ構成

```
apps/poc/phase1/src/app/research/
├── page.tsx                    # 新規分析フォーム
├── list/page.tsx               # 分析履歴一覧
├── status/[job_id]/page.tsx    # ステータス確認（ポーリング）
└── result/[job_id]/page.tsx    # 結果表示
```

### ステータスページ（ポーリング実装）

```typescript
// apps/poc/phase1/src/app/research/status/[job_id]/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function StatusPage({ params }: { params: { job_id: string } }) {
  const router = useRouter();
  const [status, setStatus] = useState<StatusData | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const MAX_POLL_ATTEMPTS = 30; // 15分 (30回 × 30秒)

  // リトライ処理
  const handleRetry = async () => {
    const res = await fetch(`/api/analyze/retry/${params.job_id}`, {
      method: 'POST',
    });
    const data = await res.json();
    setStatus(data);
    setPollCount(0); // ポーリングカウントをリセット
  };

  useEffect(() => {
    const pollStatus = async () => {
      const res = await fetch(`/api/analyze/status/${params.job_id}`);
      const data = await res.json();
      setStatus(data);
      setPollCount(prev => prev + 1);

      // タイムアウトチェック
      if (pollCount >= MAX_POLL_ATTEMPTS && data.status === 'researching') {
        return; // ポーリング停止
      }

      // 完了したら結果ページへ遷移
      if (data.status === 'completed') {
        router.push(`/research/result/${params.job_id}`);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 30000); // 30秒ごとにポーリング
    return () => clearInterval(interval);
  }, [params.job_id, router, pollCount]);

  return (
    <div>
      <p>{getStatusText(status?.status)}</p>
      {status?.status === 'failed' && (
        <button onClick={handleRetry}>もう一度分析を実行</button>
      )}
    </div>
  );
}
```

### 一覧ページ（React Query使用）

```typescript
// apps/poc/phase1/src/app/research/list/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';

export default function ListPage() {
  const { data, refetch } = useQuery<ListResponse>({
    queryKey: ['jobs', selectedStatus],
    queryFn: async () => {
      const res = await fetch(`/api/analyze/list?limit=50`);
      return res.json();
    },
    refetchInterval: 60000, // 1分ごとに自動更新
  });

  return (
    <div>
      {data?.jobs.map((job) => (
        <Link
          key={job.job_id}
          href={job.status === 'completed'
            ? `/research/result/${job.job_id}`
            : `/research/status/${job.job_id}`
          }
        >
          {job.patent_number} - {statusLabels[job.status]}
        </Link>
      ))}
    </div>
  );
}
```

:::info ポーリング仕様
- **ステータスページ**: 30秒間隔、最大15分（30回）でタイムアウト
- **一覧ページ**: 1分間隔で自動更新（React Query使用）
:::

---

## 🔧 環境変数設定

### Vercel環境変数

```bash
# ===== データベース（Prisma） =====
# DATABASE_URL: Prisma Client用（pgbouncer経由）
DATABASE_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:6543/postgres?schema=production&pgbouncer=true
# DIRECT_URL: マイグレーション用（直接接続）
DIRECT_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:5432/postgres?schema=production

# ===== LLMプロバイダー =====
# LLM_PROVIDER: openai | claude（デフォルト: openai）
LLM_PROVIDER=openai
# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_DEEP_RESEARCH_MODEL=o4-mini-deep-research-2025-06-26
# Claude API（LLM_PROVIDER=claude の場合）
ANTHROPIC_API_KEY=sk-ant-xxxxx

# ===== 検索プロバイダー =====
# SEARCH_PROVIDER: dummy | tavily（デフォルト: dummy）
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-xxxxx

# ===== モデル設定 =====
# OpenAI: gpt-4o-mini | gpt-4o | o4-mini-deep-research-2025-06-26
# Claude: claude-3-5-sonnet-20241022 | claude-3-opus-20240229
MODEL_NAME=o4-mini-deep-research-2025-06-26
MAX_TOKENS=2000
TEMPERATURE=0.3

# ===== OpenAI Webhook =====
OPENAI_WEBHOOK_SECRET=whsec_xxxxx
OPENAI_WEBHOOK_URL=https://ip-rich-poc-phase1.vercel.app/api/webhook/openai

# ===== Cron設定 =====
CRON_SECRET_KEY=your-secure-random-string
MAX_CONCURRENT_JOBS=3

# ===== Basic認証 =====
BASIC_AUTH_USERNAME=patent
BASIC_AUTH_PASSWORD=xxxxx
SKIP_AUTH=false  # 開発環境では true

# ===== Next.js =====
NEXT_PUBLIC_APP_URL=https://ip-rich-poc-phase1.vercel.app
```

:::tip プロバイダー切り替え
`LLM_PROVIDER` と `SEARCH_PROVIDER` を変更することで、バックエンドの実装を変更せずにプロバイダーを切り替えられます。
:::

### GitHub Secrets

```
CRON_SECRET_KEY        # Cronエンドポイント認証
BASIC_AUTH_USERNAME    # Basic認証ユーザー名
BASIC_AUTH_PASSWORD    # Basic認証パスワード
```

---

## 💰 コスト試算

```
Supabase無料枠:
  - データベース: 500MB（無料）
  - API呼び出し: 制限なし
  - ストレージ: 1GB（無料）

OpenAI Deep Research:
  - 使用量に応じた従量課金
  - 1件あたり約$0.10〜$0.50（検索量による）

GitHub Actions:
  - 2,000分/月（無料枠）
  - 15分×4回/時×24時間×30日 = 43,200分必要
  - → 実際は条件分岐で削減可能

Vercel:
  - Hobby: $0（無料）
  - Pro: $20/月（商用利用時）

月額コスト目安:
  - 開発中: $0〜$5
  - 本番運用: $20〜$50
```

---

## ✅ 実装完了チェックリスト

- [x] Supabase PostgreSQL + Prisma設定
- [x] Next.js APIルート実装
  - [x] /api/analyze/start（ジョブ作成）
  - [x] /api/analyze/status/[job_id]（ステータス確認 + 自動保存）
  - [x] /api/analyze/result/[job_id]（結果取得）
  - [x] /api/analyze/list（一覧取得）
  - [x] /api/analyze/retry/[job_id]（失敗ジョブのリトライ）
  - [x] /api/patent-search/schedule（スケジュール登録）
  - [x] /api/cron/check-and-do（バッチ処理）
  - [x] /api/webhook/openai（Webhook受信）
- [x] OpenAI Deep Research API統合
- [x] Webhook署名検証
- [x] GitHub Actions Cron設定
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

## 📚 関連資料

- [Phase 1 実装計画](./phase1-implementation-plan.md)
- [特許侵害調査ワークフロー](./patent-workflow.md)
- [OpenAI Deep Research API Docs](https://platform.openai.com/docs)
- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Prisma公式ドキュメント](https://www.prisma.io/docs)

---

## 🔮 今後の拡張案

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

:::tip v1.1アーキテクチャのメリット

- ✅ Vercelタイムアウト制限を回避（非同期処理）
- ✅ OpenAI Deep Research API直接利用（別サービス不要）
- ✅ GitHub Actions / Vercel Cronで定期実行
- ✅ Webhookで確実に結果を受信
- ✅ Polling（フォールバック）で信頼性向上
- ✅ Prismaによる型安全なDB操作
- ✅ 完全無料枠での運用可能
:::
