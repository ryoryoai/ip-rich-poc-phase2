---
sidebar_position: 5
---

# PoC開発計画 v1.1（非同期処理対応版）

Vercelの300秒タイムアウト制限に対応するため、Deep Researchを非同期処理化したアーキテクチャに移行します。

## 📋 v1.0からの主な変更点

| 項目               | v1.0（同期処理）       | v1.1（非同期処理）            |
| ------------------ | ---------------------- | ----------------------------- |
| **Deep Research**  | Next.js API内で実行    | 外部サービス + Webhook        |
| **タイムアウト**   | 300秒（5分）で強制終了 | 15分以上対応可能              |
| **データベース**   | ローカルJSON           | Supabase/Neon（無料）         |
| **ステータス管理** | なし                   | ポーリング + ジョブ管理       |
| **フロントエンド** | 同期待機               | ポーリング + リアルタイム更新 |

:::danger Vercelタイムアウト制限
Vercel無料プランでは、APIルートは**300秒（5分）**で強制終了します。Deep Researchは5〜15分かかるため、**v1.0のアーキテクチャでは動作しません**。
:::

---

## 🏗️ v1.1 アーキテクチャ概要

### システム構成図（現在の実装）

```
┌─────────────┐
│   ユーザー   │
└──────┬──────┘
       │ 1. 分析リクエスト
       ▼
┌─────────────────────────┐
│   Next.js Frontend      │
│   (Vercel)              │
└──────┬──────────────────┘
       │ 2. POST /api/analyze/start (pending作成)
       ▼
┌─────────────────────────┐         ┌──────────────────┐
│   Next.js API Routes    │◄────────┤  Supabase        │
│   (Vercel)              │         │  PostgreSQL      │
│                         │         │  + Prisma ORM    │
│ - /api/analyze/start    │         └──────────────────┘
│ - /api/analyze/status   │
│ - /api/analyze/result   │
│ - /api/cron/check-and-do│
│ - /api/webhook/openai   │
└──────┬──────────────────┘
       │ 3. Cronジョブ実行
       ▼
┌─────────────────────────┐
│  Cron Job               │
│  /api/cron/check-and-do │
│                         │
│  - pendingジョブ取得    │
│  - OpenAI API呼び出し   │
│  - status更新           │
└──────┬──────────────────┘
       │ 4. Deep Research実行
       ▼
┌─────────────────────────┐
│  OpenAI Deep Research   │
│  (background: true)     │
│                         │
│  - o4-mini-deep-research│
│  - 5-15分で実行         │
│  - Webhook/Polling      │
└──────┬──────────────────┘
       │ 5. 結果保存
       ▼
┌─────────────────────────┐
│   Database更新          │
│   status → completed    │
└─────────────────────────┘
```

### 処理フロー（実際の実装）

```mermaid
graph LR
    A[ユーザー] -->|1. 分析開始| B[/api/analyze/start]
    B -->|2. ジョブ作成| C[DB: pending]
    B -->|3. job_id返却| A

    D[Cron Job] -->|4. 定期実行| E[/api/cron/check-and-do]
    E -->|5. pendingジョブ取得| C
    E -->|6. OpenAI Deep Research開始| F[OpenAI API]
    E -->|7. status更新| C[DB: researching]

    F -->|8. バックグラウンド処理| F
    E -->|9. ポーリングで確認| F
    F -->|10. 完了| E
    E -->|11. 結果保存| C[DB: completed]

    A -->|12. ステータス確認| G[/api/analyze/status]
    G -->|13. 状態返却| C
    A -->|14. 結果取得| H[/api/analyze/result]
    H -->|15. 結果返却| C
```

---

## 🗄️ データベース設計

### 推奨DB: Supabase vs Neon比較

| 項目             | Supabase（推奨）    | Neon                 | PlanetScale          |
| ---------------- | ------------------- | -------------------- | -------------------- |
| **データベース** | PostgreSQL          | PostgreSQL           | MySQL/PostgreSQL     |
| **無料枠**       | 500MB + 1GB Storage | 10 branches, 1GB RAM | 有料のみ（$34/月〜） |
| **認証機能**     | ✅ 組み込み         | ❌ なし              | ❌ なし              |
| **リアルタイム** | ✅ あり             | ❌ なし              | ❌ なし              |
| **API自動生成**  | ✅ REST + GraphQL   | ❌ なし              | ❌ なし              |
| **Vercel統合**   | ✅ 簡単             | ✅ 簡単              | ✅ 簡単              |
| **ローカル開発** | Docker Compose      | Docker/PostgreSQL    | Docker/MySQL         |
| **料金体系**     | 無料〜$25/月        | 無料〜$69/月         | $34/月〜             |

**推奨**: **Supabase**

- 認証、API、リアルタイム機能が全て無料枠に含まれる
- Next.jsとの統合が公式にサポートされている
- 将来的にリアルタイム通知機能を追加しやすい

### Supabaseテーブルスキーマ

```sql
-- 分析ジョブテーブル
CREATE TABLE analysis_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- ジョブステータス
  status TEXT NOT NULL CHECK (status IN ('pending', 'researching', 'analyzing', 'completed', 'failed')),
  progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  error_message TEXT,

  -- 入力データ
  patent_number TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  company_name TEXT NOT NULL,
  product_name TEXT NOT NULL,

  -- Deep Research結果
  research_results JSONB,

  -- 分析結果
  requirements JSONB,
  compliance_results JSONB,
  summary JSONB,

  -- メタデータ
  user_id UUID, -- 将来的な認証対応
  ip_address TEXT
);

-- インデックス
CREATE INDEX idx_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_jobs_created_at ON analysis_jobs(created_at DESC);
CREATE INDEX idx_jobs_user_id ON analysis_jobs(user_id);

-- 自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_jobs_updated_at
BEFORE UPDATE ON analysis_jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
```

### ローカル開発環境

#### オプション1: Supabase CLI（推奨）

```bash
# Supabase CLIインストール
npm install -g supabase

# ローカルSupabaseインスタンス起動
supabase init
supabase start

# マイグレーション適用
supabase db push

# ローカルURL: http://localhost:54321
# PostgreSQL: postgresql://postgres:postgres@localhost:54322/postgres
```

#### オプション2: Docker PostgreSQL

```yaml
# docker-compose.yml
version: "3.8"
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ip_rich_tools
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# 起動
docker-compose up -d

# 接続文字列
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ip_rich_tools
```

---

## 🔄 Deep Researchサービスの実装

### オプション1: Render.com無料枠（推奨）

**特徴**:

- 無料プランで750時間/月の稼働時間
- タイムアウト: 15分（Vercelの3倍）
- 自動デプロイ（GitHub連携）

**コスト**: $0/月（無料枠内）

```typescript
// deep-research-service/src/index.ts
import express from "express";
import axios from "axios";

const app = express();
app.use(express.json());

interface ResearchRequest {
  job_id: string;
  webhook_url: string;
  query: string;
  max_results?: number;
}

app.post("/research/start", async (req, res) => {
  const { job_id, webhook_url, query, max_results = 5 }: ResearchRequest = req.body;

  // すぐにレスポンス（非同期処理開始）
  res.status(202).json({ status: "accepted", job_id });

  // バックグラウンドで処理
  (async () => {
    try {
      // Tavily Deep Research API呼び出し
      const tavilyResponse = await axios.post(
        "https://api.tavily.com/research",
        {
          api_key: process.env.TAVILY_API_KEY,
          query,
          search_depth: "advanced",
          max_results,
        },
        {
          timeout: 900000, // 15分
        }
      );

      // Webhook送信
      await axios.post(webhook_url, {
        job_id,
        status: "completed",
        results: tavilyResponse.data,
      });
    } catch (error) {
      // エラー時もWebhookで通知
      await axios.post(webhook_url, {
        job_id,
        status: "failed",
        error: error.message,
      });
    }
  })();
});

app.listen(3000, () => {
  console.log("Deep Research Service running on port 3000");
});
```

#### Render.comデプロイ設定

```yaml
# render.yaml
services:
  - type: web
    name: deep-research-service
    env: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: TAVILY_API_KEY
        sync: false
    plan: free
```

### オプション2: Railway無料枠

**特徴**:

- 無料プランで500時間/月 + $5クレジット
- タイムアウト制限なし
- 自動スケーリング

**コスト**: $0〜5/月（無料クレジット内）

### オプション3: Fly.io無料枠

**特徴**:

- 3つのVMを無料で提供
- タイムアウト制限なし
- グローバルデプロイ

**コスト**: $0/月（無料枠内）

---

## 🔌 Next.js APIエンドポイント設計

### 1. `POST /api/analyze/start` - 分析開始

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
  status: "pending";
  created_at: string;
}
```

**実装例**:

```typescript
// apps/poc/phase1/src/app/api/analyze/start/route.ts
import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { patentNumber, claimText, companyName, productName } = body;

  // Supabaseクライアント
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  // プロンプトを生成（cronジョブで使用するため事前に保存）
  const query = buildInfringementPrompt(patentNumber, claimText);

  // ジョブ作成（Prisma使用）
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

### 2. `GET /api/analyze/status/:job_id` - ステータス確認

**レスポンス**:

```typescript
interface AnalyzeStatusResponse {
  job_id: string;
  status: "pending" | "researching" | "analyzing" | "completed" | "failed";
  progress: number; // 0-100
  error_message?: string;
}
```

**実装例**:

```typescript
// apps/poc/phase1/src/app/api/analyze/status/[job_id]/route.ts
export async function GET(request: NextRequest, { params }: { params: { job_id: string } }) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  const { data: job, error } = await supabase
    .from("analysis_jobs")
    .select("id, status, progress, error_message")
    .eq("id", params.job_id)
    .single();

  if (error || !job) {
    return NextResponse.json({ error: "Job not found" }, { status: 404 });
  }

  return NextResponse.json({
    job_id: job.id,
    status: job.status,
    progress: job.progress,
    error_message: job.error_message,
  });
}
```

### 3. `GET /api/analyze/result/:job_id` - 結果取得

**レスポンス**:

```typescript
interface AnalyzeResultResponse {
  job_id: string;
  status: "completed";
  result: {
    patentNumber: string;
    companyName: string;
    productName: string;
    requirements: Requirement[];
    complianceResults: ComplianceResult[];
    summary: {
      totalRequirements: number;
      compliantRequirements: number;
      complianceRate: number;
      infringementPossibility: "○" | "×";
    };
  };
}
```

### 4. `POST /api/webhook/research` - Webhook受信

**リクエスト**:

```typescript
interface WebhookResearchRequest {
  job_id: string;
  status: "completed" | "failed";
  results?: any;
  error?: string;
}
```

**実装例**:

```typescript
// apps/poc/phase1/src/app/api/webhook/research/route.ts
export async function POST(request: NextRequest) {
  const body = await request.json();
  const { job_id, status, results, error } = body;

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  if (status === "failed") {
    await supabase
      .from("analysis_jobs")
      .update({ status: "failed", error_message: error })
      .eq("id", job_id);

    return NextResponse.json({ status: "error_recorded" });
  }

  // 検索結果を保存
  await supabase
    .from("analysis_jobs")
    .update({
      research_results: results,
      status: "analyzing",
      progress: 50,
    })
    .eq("id", job_id);

  // LLM分析を開始（別関数で実行）
  await performLLMAnalysis(job_id);

  return NextResponse.json({ status: "processing" });
}

async function performLLMAnalysis(job_id: string) {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  // ジョブ情報取得
  const { data: job } = await supabase.from("analysis_jobs").select("*").eq("id", job_id).single();

  if (!job) return;

  // 既存のLLM分析ロジックを実行
  const llmProvider = getLLMProvider();
  const requirementService = new RequirementExtractionService(llmProvider);

  const requirements = await requirementService.extractRequirements(
    job.patent_number,
    job.claim_text
  );

  await supabase.from("analysis_jobs").update({ requirements, progress: 70 }).eq("id", job_id);

  // 充足性判定
  const searchProvider = getSearchProvider();
  const complianceService = new ComplianceCheckService(llmProvider, searchProvider);

  const complianceResults = await Promise.all(
    requirements.map((req) =>
      complianceService.checkCompliance(req, job.product_name, job.company_name)
    )
  );

  // 総合判定
  const compliantCount = complianceResults.filter((r) => r.compliance === "○").length;
  const summary = {
    totalRequirements: requirements.length,
    compliantRequirements: compliantCount,
    complianceRate: (compliantCount / requirements.length) * 100,
    infringementPossibility: compliantCount === requirements.length ? "○" : "×",
  };

  // 最終結果保存
  await supabase
    .from("analysis_jobs")
    .update({
      compliance_results: complianceResults,
      summary,
      status: "completed",
      progress: 100,
    })
    .eq("id", job_id);
}
```

---

## 🎨 フロントエンド実装（ポーリング対応）

### ポーリングコンポーネント

```typescript
// apps/poc/phase1/src/components/AnalysisProgress.tsx
'use client';

import { useEffect, useState } from 'react';

interface AnalysisProgressProps {
  jobId: string;
  onComplete: (result: any) => void;
}

export function AnalysisProgress({ jobId, onComplete }: AnalysisProgressProps) {
  const [status, setStatus] = useState<string>('pending');
  const [progress, setProgress] = useState<number>(0);

  useEffect(() => {
    const pollInterval = setInterval(async () => {
      const res = await fetch(`/api/analyze/status/${jobId}`);
      const data = await res.json();

      setStatus(data.status);
      setProgress(data.progress);

      if (data.status === 'completed') {
        clearInterval(pollInterval);

        // 結果を取得
        const resultRes = await fetch(`/api/analyze/result/${jobId}`);
        const result = await resultRes.json();
        onComplete(result);
      } else if (data.status === 'failed') {
        clearInterval(pollInterval);
        alert('分析に失敗しました: ' + data.error_message);
      }
    }, 10000); // 10秒ごとにポーリング

    return () => clearInterval(pollInterval);
  }, [jobId, onComplete]);

  const getStatusText = () => {
    switch (status) {
      case 'pending': return '分析を開始しています...';
      case 'researching': return '製品情報を検索中...';
      case 'analyzing': return 'AI分析を実行中...';
      case 'completed': return '分析完了！';
      case 'failed': return '分析に失敗しました';
      default: return '処理中...';
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <p className="text-lg font-medium">{getStatusText()}</p>
        <p className="text-sm text-gray-500">ジョブID: {jobId}</p>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-blue-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="text-sm text-gray-600">{progress}% 完了</p>
    </div>
  );
}
```

### 分析開始ページ

```typescript
// apps/poc/phase1/src/app/analyze/page.tsx
'use client';

import { useState } from 'react';
import { AnalysisProgress } from '@/components/AnalysisProgress';

export default function AnalyzePage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    const res = await fetch('/api/analyze/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patentNumber: formData.get('patentNumber'),
        claimText: formData.get('claimText'),
        companyName: formData.get('companyName'),
        productName: formData.get('productName'),
      }),
    });

    const data = await res.json();
    setJobId(data.job_id);
  };

  if (result) {
    return <div>結果表示: {JSON.stringify(result, null, 2)}</div>;
  }

  if (jobId) {
    return <AnalysisProgress jobId={jobId} onComplete={setResult} />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input name="patentNumber" placeholder="特許番号" required />
      <textarea name="claimText" placeholder="請求項1" required />
      <input name="companyName" placeholder="企業名" required />
      <input name="productName" placeholder="製品名" required />
      <button type="submit">分析開始</button>
    </form>
  );
}
```

---

## 📦 必要な依存関係

### Next.jsプロジェクト（apps/poc/phase1/）

```bash
# Supabaseクライアント
npm install @supabase/supabase-js

# 既存の依存関係は継続
npm install @anthropic-ai/sdk openai axios zod
```

### Deep Researchサービス（新規プロジェクト）

```bash
mkdir deep-research-service
cd deep-research-service
npm init -y

npm install express axios dotenv
npm install -D typescript @types/express @types/node tsx
```

---

## 🚀 実装ステップ（v1.1移行）

| ステップ | 作業内容                      | 期間     | 成果物                          |
| -------- | ----------------------------- | -------- | ------------------------------- |
| 1        | **Supabaseセットアップ**      | 1日      | テーブル作成、ローカル環境構築  |
| 2        | **Deep Researchサービス開発** | 2日      | Render.comデプロイ準備          |
| 3        | **Next.js API改修**           | 3日      | start/status/result/webhook実装 |
| 4        | **フロントエンド改修**        | 2日      | ポーリングUI実装                |
| 5        | **統合テスト**                | 2日      | E2Eテスト、負荷テスト           |
| **合計** | -                             | **10日** | 完全非同期対応システム          |

---

## 💰 コスト試算（v1.1）

```
Supabase無料枠:
  - データベース: 500MB（無料）
  - API呼び出し: 50,000/月（無料）
  - ストレージ: 1GB（無料）

Render.com無料枠:
  - 稼働時間: 750時間/月（無料）
  - Deep Researchサービス: $0

Claude API:
  - 構成要件抽出: $0.09（無料枠内）
  - 充足性判定: $0.18（無料枠内）

Tavily API:
  - 1000検索/月（無料）

Vercel:
  - Next.jsホスティング: $0（無料枠）

合計コスト: $0（完全無料）
```

---

## 📊 シーケンス図

![非同期処理ワークフロー](./diagrams/async-workflow-v1.1.svg)

シーケンス図は`docs-site/docs/diagrams/async-workflow-v1.1.puml`を参照してください。

---

## 🔧 環境変数設定

### Next.js（.env.local）

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Deep Research Service
DEEP_RESEARCH_SERVICE_URL=https://deep-research-service.onrender.com
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app

# LLM Provider
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-xxxxx

# Search Provider
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-xxxxx
```

### Deep Research Service（.env）

```bash
TAVILY_API_KEY=tvly-xxxxx
PORT=3000
```

---

## ✅ テスト計画

### 1. ユニットテスト

```typescript
// tests/api/analyze/start.test.ts
describe("POST /api/analyze/start", () => {
  it("should create a job and return job_id", async () => {
    const res = await fetch("/api/analyze/start", {
      method: "POST",
      body: JSON.stringify({
        patentNumber: "JP1234567",
        claimText: "テスト請求項",
        companyName: "テスト企業",
        productName: "テスト製品",
      }),
    });

    const data = await res.json();
    expect(data.job_id).toBeDefined();
    expect(data.status).toBe("pending");
  });
});
```

### 2. E2Eテスト（Playwright）

```typescript
// tests/e2e/analysis-flow.spec.ts
import { test, expect } from "@playwright/test";

test("full analysis workflow", async ({ page }) => {
  await page.goto("/analyze");

  // フォーム入力
  await page.fill('[name="patentNumber"]', "JP1234567");
  await page.fill('[name="claimText"]', "テスト請求項");
  await page.fill('[name="companyName"]', "テスト企業");
  await page.fill('[name="productName"]', "テスト製品");

  // 分析開始
  await page.click('button[type="submit"]');

  // ジョブID表示確認
  await expect(page.locator("text=ジョブID:")).toBeVisible();

  // ポーリング待機（最大15分）
  await page.waitForSelector("text=分析完了！", { timeout: 900000 });

  // 結果表示確認
  await expect(page.locator("text=侵害可能性")).toBeVisible();
});
```

---

## 🎯 移行チェックリスト

- [ ] Supabaseアカウント作成 + プロジェクト作成
- [ ] Supabaseローカル環境セットアップ（`supabase start`）
- [ ] テーブルスキーマ適用（`analysis_jobs`テーブル作成）
- [ ] Render.comアカウント作成
- [ ] Deep Researchサービスリポジトリ作成
- [ ] Deep ResearchサービスをRender.comにデプロイ
- [ ] Next.js APIルート改修（start/status/result/webhook）
- [ ] フロントエンドポーリング機能実装
- [ ] 環境変数設定（Vercel + Render.com）
- [ ] E2Eテスト実行
- [ ] 本番デプロイ

---

## 📚 関連資料

- [非同期処理シーケンス図](./diagrams/async-workflow-v1.1.puml)
- [Phase 1 PoC開発計画（v1.0）](./poc-development-plan.md)
- [特許侵害調査ワークフロー](./patent-workflow.md)
- [Supabase公式ドキュメント](https://supabase.com/docs)
- [Render.com公式ドキュメント](https://render.com/docs)
- [Tavily API Documentation](https://docs.tavily.com/)

---

## 🔮 今後の拡張案

### v1.2: リアルタイム通知対応

- Supabase Realtimeを使用したWebSocket通知
- ポーリングの代わりにプッシュ通知

### v1.3: バッチ処理対応

- 複数特許の一括分析
- バックグラウンドジョブキュー（BullMQ）

### v1.4: ユーザー認証・マルチテナント

- Supabase Authでユーザー管理
- 分析履歴の保存・検索機能

---

:::tip v1.1のメリット

- ✅ Vercelタイムアウト制限を回避（15分以上対応可能）
- ✅ 完全無料枠内で運用可能（Supabase + Render.com）
- ✅ ポーリングによる進捗表示でUX向上
- ✅ Deep Researchを外部サービス化して再利用可能
- ✅ 将来的なリアルタイム通知への移行が容易
  :::
