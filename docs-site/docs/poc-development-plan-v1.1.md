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
│   /api/patent-search/   │
│     schedule            │
└──────┬──────────────────┘
       │ 2. ジョブ作成
       ▼
┌─────────────────────────┐         ┌──────────────────┐
│   Next.js API Routes    │◄────────┤  Supabase        │
│   (Vercel)              │         │  PostgreSQL      │
│                         │         │  (Prisma)        │
│ - /api/analyze/start    │         └──────────────────┘
│ - /api/analyze/status   │
│ - /api/analyze/result   │
│ - /api/analyze/list     │
│ - /api/cron/check-and-do│
│ - /api/webhook/openai   │
└──────┬──────────────────┘
       │ 3. Deep Research依頼
       │    (background: true)
       ▼
┌─────────────────────────┐
│  OpenAI Deep Research   │
│  API                    │
│                         │
│  - o4-mini-deep-research│
│  - Web検索機能内蔵      │
│  - 非同期処理           │
└──────┬──────────────────┘
       │ 4. Webhook (結果返却)
       ▼
┌─────────────────────────┐
│   /api/webhook/openai   │
│   結果をPrismaに保存    │
└─────────────────────────┘

        ↑
        │ 15分ごと
┌─────────────────────────┐
│   GitHub Actions Cron   │
│   /api/cron/check-and-do│
│   - ステータス確認      │
│   - 新規ジョブ開始      │
└─────────────────────────┘
```

### 処理フロー

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant N as Next.js API
    participant DB as PostgreSQL
    participant O as OpenAI API
    participant C as GitHub Actions

    U->>N: POST /api/analyze/start
    N->>DB: ジョブ作成 (status: pending)
    N->>O: Deep Research (background: true)
    O-->>N: response.id
    N->>DB: ステータス更新 (researching)
    N-->>U: job_id

    U->>N: GET /api/analyze/status/:id
    N->>DB: ステータス取得
    DB-->>N: status, progress
    N-->>U: 進捗状況

    Note over O: Deep Research実行中...

    O->>N: POST /api/webhook/openai
    N->>DB: 結果保存 (completed)

    U->>N: GET /api/analyze/result/:id
    N->>DB: 結果取得
    DB-->>N: research_results
    N-->>U: 分析結果

    Note over C: 15分ごとにCron実行
    C->>N: POST /api/cron/check-and-do
    N->>O: ステータス確認 (polling)
    N->>DB: 必要に応じて更新
    N->>O: 新規ジョブ開始
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

  // バッチ処理用
  priority      Int       @default(5)
  scheduledFor  DateTime? @map("scheduled_for") @db.Timestamptz(6)
  retryCount    Int       @default(0) @map("retry_count")
  maxRetries    Int       @default(3) @map("max_retries")
  searchType    String    @default("infringement_check") @map("search_type") @db.Text

  // タイムスタンプ
  startedAt   DateTime? @map("started_at") @db.Timestamptz(6)
  finishedAt  DateTime? @map("finished_at") @db.Timestamptz(6)

  @@index([status], map: "idx_jobs_status")
  @@index([createdAt(sort: Desc)], map: "idx_jobs_created_at")
  @@index([status, priority, scheduledFor], map: "idx_jobs_queue")
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

### 非同期呼び出し

```typescript
// apps/poc/phase1/src/app/api/analyze/start/route.ts
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

// response.idをDBに保存してWebhookで照合
await prisma.analysis_jobs.update({
  where: { id: job.id },
  data: {
    status: 'researching',
    openaiResponseId: response.id,
  },
});
```

### Webhook受信

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

### Cronハンドラーの処理内容

```typescript
// apps/poc/phase1/src/app/api/cron/check-and-do/route.ts
export async function POST(request: NextRequest) {
  // 認証
  if (cronSecret !== process.env.CRON_SECRET_KEY) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // 1. 実行中ジョブのステータス確認
  const inProgressJobs = await prisma.analysis_jobs.findMany({
    where: { status: 'researching' },
  });

  for (const job of inProgressJobs) {
    const response = await openai.responses.retrieve(job.openaiResponseId);
    if (response.status === 'completed') {
      // 結果を保存
      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: { status: 'completed', researchResults: response.output },
      });
    }
  }

  // 2. 新規ジョブの開始
  const maxConcurrent = parseInt(process.env.MAX_CONCURRENT_JOBS || '3');
  const currentRunning = await prisma.analysis_jobs.count({
    where: { status: 'researching' },
  });

  if (currentRunning < maxConcurrent) {
    const pendingJobs = await prisma.analysis_jobs.findMany({
      where: { status: 'pending' },
      orderBy: [{ priority: 'desc' }, { createdAt: 'asc' }],
      take: maxConcurrent - currentRunning,
    });

    for (const job of pendingJobs) {
      // Deep Research開始
      const response = await openai.responses.create({
        model: 'o4-mini-deep-research-2025-06-26',
        input: [{ type: 'message', role: 'user', content: buildQuery(job) }],
        background: true,
      });

      await prisma.analysis_jobs.update({
        where: { id: job.id },
        data: { status: 'researching', openaiResponseId: response.id },
      });
    }
  }
}
```

---

## 🎨 フロントエンド実装

### ポーリングコンポーネント

```typescript
// apps/poc/phase1/src/components/AnalysisProgress.tsx
'use client';

import { useEffect, useState } from 'react';

export function AnalysisProgress({ jobId, onComplete }) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      const res = await fetch(`/api/analyze/status/${jobId}`);
      const data = await res.json();

      setStatus(data.status);
      setProgress(data.progress);

      if (data.status === 'completed') {
        clearInterval(pollInterval);
        const result = await fetch(`/api/analyze/result/${jobId}`);
        onComplete(await result.json());
      } else if (data.status === 'failed') {
        clearInterval(pollInterval);
      }
    }, 10000); // 10秒ごとにポーリング

    return () => clearInterval(pollInterval);
  }, [jobId, onComplete]);

  return (
    <div>
      <p>{getStatusText(status)}</p>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-blue-600 h-4 rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

---

## 🔧 環境変数設定

### Vercel環境変数

```bash
# データベース（Prisma）
DATABASE_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:6543/postgres?schema=production&pgbouncer=true
DIRECT_URL=postgresql://postgres.[ref]:[password]@pooler.supabase.com:5432/postgres?schema=production

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
  - [x] /api/analyze/start
  - [x] /api/analyze/status/[job_id]
  - [x] /api/analyze/result/[job_id]
  - [x] /api/analyze/list
  - [x] /api/patent-search/schedule
  - [x] /api/cron/check-and-do
  - [x] /api/webhook/openai
- [x] OpenAI Deep Research API統合
- [x] Webhook署名検証
- [x] GitHub Actions Cron設定
- [x] フロントエンドポーリング実装
- [x] 環境変数設定（Vercel）
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
- ✅ GitHub Actions Cronで定期実行
- ✅ Webhookで確実に結果を受信
- ✅ Prismaによる型安全なDB操作
- ✅ 完全無料枠での運用可能
:::
