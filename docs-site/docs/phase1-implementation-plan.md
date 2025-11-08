---
sidebar_position: 5
---

# Phase 1: 侵害調査自動化 - 実装計画

Phase 1（侵害調査の自動化）の詳細な実装計画です。

## 概要

**期間**: 2〜3週間（13営業日）
**目標**: 特許1件あたりの侵害可能性を自動判定するシステムを構築
**コスト**: $0.02〜1/月

## プロジェクト構造（Next.js版）

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
            ├── .gitignore
            ├── src/
            │   ├── app/             # Next.js App Router
            │   │   ├── layout.tsx
            │   │   ├── page.tsx
            │   │   ├── analyze/
            │   │   │   └── page.tsx
            │   │   └── api/
            │   │       ├── analyze/
            │   │       │   └── route.ts
            │   │       ├── requirements/
            │   │       │   └── route.ts
            │   │       └── compliance/
            │   │           └── route.ts
            │   ├── components/
            │   │   ├── ui/          # shadcn/ui
            │   │   │   ├── button.tsx
            │   │   │   ├── card.tsx
            │   │   │   ├── input.tsx
            │   │   │   └── textarea.tsx
            │   │   ├── PatentInputForm.tsx
            │   │   ├── RequirementsList.tsx
            │   │   ├── ComplianceResults.tsx
            │   │   └── AnalysisReport.tsx
            │   ├── lib/
            │   │   ├── openai.ts
            │   │   ├── search.ts
            │   │   ├── storage.ts
            │   │   ├── prompts.ts
            │   │   └── utils.ts
            │   └── types/
            │       ├── patent.ts
            │       ├── analysis.ts
            │       └── api.ts
            ├── public/
            │   └── sample-data/
            │       └── patents.json
            └── data/
                ├── results/
                └── cache/
```

---

## Week 1: 基盤構築とプロンプト開発（5日間）

### Day 1-2: プロジェクト初期化とプロンプト設計

**作業内容**:

1. Next.jsプロジェクト構造の作成
2. 依存関係の定義（package.json）
3. TypeScript設定（tsconfig.json）
4. 環境変数の設定（.env.local.example）
5. プロンプトテンプレートの設計（TypeScript）
6. テスト環境のセットアップ（Jest + Playwright）

**成果物**:

- apps/poc/phase1/ プロジェクト骨格
- package.json（依存関係とスクリプト）
- tsconfig.json, next.config.js
- .env.local.example
- src/lib/prompts.ts
- テスト設定（jest.config.js, playwright.config.ts）

**package.json**:

```json
{
  "name": "phase1-infringement-analyzer",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3001",
    "build": "next build",
    "start": "next start -p 3001",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "openai": "^4.26.0",
    "axios": "^1.6.5",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.321.0",
    "tailwind-merge": "^2.2.1",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@types/jest": "^29.5.11",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0",
    "@playwright/test": "^1.41.0",
    "eslint": "^8",
    "eslint-config-next": "14.1.0"
  }
}
```

**jest.config.js**:

```javascript
const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testMatch: ["**/__tests__/**/*.ts?(x)", "**/?(*.)+(spec|test).ts?(x)"],
};

module.exports = createJestConfig(customJestConfig);
```

**playwright.config.ts**:

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3001",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3001",
    reuseExistingServer: !process.env.CI,
  },
});
```

**.env.local.example**:

```bash
# OpenAI API (サーバー側のみ、NEXT_PUBLIC_接頭辞禁止)
OPENAI_API_KEY=your_openai_api_key_here

# Perplexity API (Optional - 無料枠100req/日)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# SerpAPI (Optional - 無料枠100検索/月)
SERPAPI_KEY=your_serpapi_key_here

# Settings
# モデル選択: gpt-3.5-turbo（低コスト）| gpt-4o-mini（精度重視・低コスト）| gpt-4（最高精度）
MODEL_NAME=gpt-3.5-turbo
MAX_TOKENS=2000
TEMPERATURE=0.3

# Next.js
NEXT_PUBLIC_APP_URL=http://localhost:3001
```

**モデル選択の指針**:

- **gpt-3.5-turbo**: 最低コスト（$0.0015/1K tokens）、PoC検証に推奨
- **gpt-4o-mini**: バランス型（$0.15/1M tokens input）、精度とコストの中間
- **gpt-4**: 最高精度（$30/1M tokens input）、本番環境で検討

**プロンプトテンプレート（src/lib/prompts.ts）**:

```typescript
export const PROMPTS = {
  extractRequirements: {
    system: `あなたは特許の構成要件を抽出する専門家です。
請求項1を分析し、構成要件を個別に抽出してください。`,

    user: (
      patentNumber: string,
      claimText: string
    ) => `以下の特許請求項1から、構成要件を抽出してください。
各構成要件を番号付きリストで出力してください。

【特許番号】${patentNumber}
【請求項1】
${claimText}

出力フォーマット:
1. 構成要件A: [要件の説明]
2. 構成要件B: [要件の説明]
...`,
  },

  checkCompliance: {
    system: `あなたは特許侵害の充足性を判定する専門家です。
構成要件と製品の仕様を比較し、充足性を判定してください。`,

    user: (requirement: string, productName: string, companyName: string, productSpec: string) =>
      `以下の構成要件について、製品が充足しているか判定してください。

【構成要件】
${requirement}

【製品情報】
製品名: ${productName}
企業名: ${companyName}
仕様情報: ${productSpec}

判定結果を以下の形式で出力してください:
- 充足判断: ○/×
- 理由: [判定理由を簡潔に記載]
- 根拠: [参照URLまたは具体的な製品機能]`,
  },
} as const;
```

### Day 3-4: コアライブラリの実装（TypeScript）

**作業内容**:

1. OpenAI APIクライアントの実装
2. 構成要件抽出・パースモジュールの実装
3. 型定義の作成
4. ユニットテスト（Jest）の作成

**成果物**:

- `src/lib/openai.ts` - OpenAI APIクライアント
- `src/lib/requirements.ts` - 構成要件抽出とパース
- `src/lib/storage.ts` - データ保存
- `src/types/patent.ts` - 特許関連の型定義
- `src/types/analysis.ts` - 分析結果の型定義
- `__tests__/lib/requirements.test.ts` - ユニットテスト

**型定義（src/types/patent.ts）**:

```typescript
export interface Requirement {
  id: string;
  description: string;
}

export interface PatentData {
  patentNumber: string;
  claimText: string;
}
```

**型定義（src/types/analysis.ts）**:

```typescript
import { Requirement } from "./patent";

export interface ComplianceResult {
  requirementId: string;
  requirement: string;
  compliance: "○" | "×";
  reason: string;
  evidence: string;
  urls: string[];
}

export interface AnalysisResult {
  patentNumber: string;
  companyName: string;
  productName: string;
  timestamp: string;
  requirements: Requirement[];
  complianceResults: ComplianceResult[];
  summary: {
    totalRequirements: number;
    compliantRequirements: number;
    complianceRate: number;
    infringementPossibility: "○" | "×";
  };
}
```

**サンプルコード（src/lib/openai.ts）**:

```typescript
import OpenAI from "openai";

export class OpenAIClient {
  private client: OpenAI;
  private model: string;
  private maxTokens: number;
  private temperature: number;

  constructor() {
    this.client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
    this.model = process.env.MODEL_NAME || "gpt-3.5-turbo";
    this.maxTokens = parseInt(process.env.MAX_TOKENS || "2000", 10);
    this.temperature = parseFloat(process.env.TEMPERATURE || "0.3");
  }

  async generate(systemPrompt: string, userPrompt: string, temperature?: number): Promise<string> {
    try {
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        max_tokens: this.maxTokens,
        temperature: temperature ?? this.temperature,
      });

      return response.choices[0]?.message?.content || "";
    } catch (error) {
      throw new Error(
        `OpenAI API Error: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}

// シングルトンインスタンス
export const openaiClient = new OpenAIClient();
```

**サンプルコード（src/lib/requirements.ts）**:

```typescript
import { openaiClient } from "./openai";
import { PROMPTS } from "./prompts";
import { Requirement } from "@/types/patent";

export async function extractRequirements(
  patentNumber: string,
  claimText: string
): Promise<Requirement[]> {
  const systemPrompt = PROMPTS.extractRequirements.system;
  const userPrompt = PROMPTS.extractRequirements.user(patentNumber, claimText);

  const response = await openaiClient.generate(systemPrompt, userPrompt);

  return parseRequirements(response);
}

export function parseRequirements(response: string): Requirement[] {
  const requirements: Requirement[] = [];
  const lines = response.trim().split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // "1. 構成要件A: 説明" 形式をパース
    const match = trimmed.match(/^(\d+\.?\s*|[-•]\s*)(.+?):\s*(.+)$/);
    if (match) {
      const [, , id, description] = match;
      requirements.push({
        id: id.trim(),
        description: description.trim(),
      });
    }
  }

  return requirements;
}
```

**ユニットテスト（**tests**/lib/requirements.test.ts）**:

```typescript
import { parseRequirements } from "@/lib/requirements";

describe("parseRequirements", () => {
  it("should parse requirements from GPT response", () => {
    const response = `
1. 構成要件A: サーバーとクライアント端末を含むシステム
2. 構成要件B: 遠隔制御機能を有すること
3. 構成要件C: AR表示機能を備えること
`;

    const result = parseRequirements(response);

    expect(result).toHaveLength(3);
    expect(result[0]).toEqual({
      id: "構成要件A",
      description: "サーバーとクライアント端末を含むシステム",
    });
    expect(result[2].id).toBe("構成要件C");
  });

  it("should handle empty response", () => {
    const result = parseRequirements("");
    expect(result).toEqual([]);
  });

  it("should handle bullet points", () => {
    const response = `
- 構成要件1: 第一の機能
- 構成要件2: 第二の機能
`;
    const result = parseRequirements(response);
    expect(result).toHaveLength(2);
  });
});
```

### Day 5: Web検索モジュールとテスト戦略

**作業内容**:

1. Web検索モジュールの実装（TypeScript）
2. 単体テスト（Jest）の作成と実行
3. E2Eテスト（Playwright）のセットアップ
4. 初期テスト実行とCI設定

**成果物**:

- `src/lib/search.ts` - Web検索クライアント
- `__tests__/lib/search.test.ts` - 検索モジュールのユニットテスト
- `__tests__/lib/openai.test.ts` - OpenAIクライアントのテスト
- `e2e/` - E2Eテストディレクトリ
- `jest.setup.js` - Jestセットアップ
- `.github/workflows/test.yml` - CI設定（オプション）

**テスト戦略**:

- **ユニットテスト（Jest）**: ライブラリ関数（parse系、ユーティリティ）
- **E2Eテスト（Playwright）**: UI操作、API統合、画面遷移

**サンプルコード（src/lib/search.ts）**:

```typescript
import axios from "axios";

export interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export class WebSearchClient {
  private perplexityKey: string | undefined;
  private serpapiKey: string | undefined;

  constructor() {
    this.perplexityKey = process.env.PERPLEXITY_API_KEY;
    this.serpapiKey = process.env.SERPAPI_KEY;
  }

  async search(query: string, numResults: number = 5): Promise<SearchResult[]> {
    // Perplexity APIを試す
    if (this.perplexityKey) {
      try {
        return await this.searchPerplexity(query, numResults);
      } catch (error) {
        console.error("Perplexity API failed:", error);
      }
    }

    // SerpAPIを試す
    if (this.serpapiKey) {
      try {
        return await this.searchSerpAPI(query, numResults);
      } catch (error) {
        console.error("SerpAPI failed:", error);
      }
    }

    // フォールバック: 基本的なスクレイピング
    return this.searchFallback(query, numResults);
  }

  private async searchPerplexity(query: string, numResults: number): Promise<SearchResult[]> {
    // TODO: Perplexity API実装
    throw new Error("Perplexity API not implemented");
  }

  private async searchSerpAPI(query: string, numResults: number): Promise<SearchResult[]> {
    const response = await axios.get("https://serpapi.com/search", {
      params: {
        q: query,
        api_key: this.serpapiKey,
        num: numResults,
      },
    });

    const results: SearchResult[] = [];
    for (const item of response.data.organic_results || []) {
      results.push({
        title: item.title || "",
        url: item.link || "",
        snippet: item.snippet || "",
      });
    }

    return results;
  }

  private searchFallback(query: string, numResults: number): SearchResult[] {
    console.warn(`Using fallback search for query: ${query}`);
    return [];
  }
}
```

---

## Week 2: 充足性判定とUI開発（5日間）

### Day 6-7: 充足性判定モジュールの実装

**作業内容**:

1. 充足性判定モジュールの実装
2. レポート生成モジュールの実装
3. データ保存機能の実装

**成果物**:

- `src/lib/compliance.ts` - 充足性判定モジュール
- `src/lib/storage.ts` - データ保存モジュール

**サンプルコード（src/lib/compliance.ts）**:

```typescript
import { OpenAIClient } from "./openai";
import { WebSearchClient, SearchResult } from "./search";
import { PROMPTS } from "./prompts";
import type { Requirement } from "@/types/patent";
import type { ComplianceResult } from "@/types/analysis";

export class ComplianceChecker {
  private openaiClient: OpenAIClient;
  private searchClient: WebSearchClient;

  constructor() {
    this.openaiClient = new OpenAIClient();
    this.searchClient = new WebSearchClient();
  }

  async checkCompliance(
    requirement: Requirement,
    productName: string,
    companyName: string
  ): Promise<ComplianceResult> {
    // 製品情報を検索
    const searchQuery = `${companyName} ${productName} specifications features`;
    const searchResults = await this.searchClient.search(searchQuery, 3);

    // 検索結果を製品仕様として整理
    const productSpec = this.formatSearchResults(searchResults);

    // GPTで充足性を判定
    const systemPrompt = PROMPTS.checkCompliance.system;
    const userPrompt = PROMPTS.checkCompliance.user(
      requirement.description,
      productName,
      companyName,
      productSpec
    );

    const response = await this.openaiClient.generate(systemPrompt, userPrompt);

    // レスポンスをパース
    const judgment = this.parseJudgment(response);

    return {
      requirementId: requirement.id,
      requirement: requirement.description,
      compliance: judgment.compliance,
      reason: judgment.reason,
      evidence: judgment.evidence,
      urls: searchResults.map((r) => r.url),
    };
  }

  private formatSearchResults(results: SearchResult[]): string {
    return results.map((result, i) => `${i + 1}. ${result.title}\n${result.snippet}`).join("\n\n");
  }

  private parseJudgment(response: string): {
    compliance: "○" | "×";
    reason: string;
    evidence: string;
  } {
    const lines = response.trim().split("\n");
    const judgment = {
      compliance: "×" as "○" | "×",
      reason: "",
      evidence: "",
    };

    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.includes("充足判断") || trimmedLine.toLowerCase().includes("compliance")) {
        if (trimmedLine.includes("○")) {
          judgment.compliance = "○";
        } else if (trimmedLine.includes("×")) {
          judgment.compliance = "×";
        }
      } else if (trimmedLine.includes("理由") || trimmedLine.toLowerCase().includes("reason")) {
        judgment.reason = trimmedLine.includes(":")
          ? trimmedLine.split(":", 2)[1].trim()
          : trimmedLine;
      } else if (trimmedLine.includes("根拠") || trimmedLine.toLowerCase().includes("evidence")) {
        judgment.evidence = trimmedLine.includes(":")
          ? trimmedLine.split(":", 2)[1].trim()
          : trimmedLine;
      }
    }

    return judgment;
  }
}

// ヘルパー関数
export async function checkCompliance(
  requirement: Requirement,
  productName: string,
  companyName: string
): Promise<ComplianceResult> {
  const checker = new ComplianceChecker();
  return checker.checkCompliance(requirement, productName, companyName);
}
```

### Day 8-9: Next.js UIの開発

**作業内容**:

1. Next.jsページとレイアウトの実装
2. shadcn/uiコンポーネントの統合
3. 分析ページとフォームの実装
4. Playwrightで動作確認

**成果物**:

- `src/app/layout.tsx` - ルートレイアウト
- `src/app/page.tsx` - トップページ
- `src/app/analyze/page.tsx` - 分析ページ
- `src/components/PatentInputForm.tsx` - 特許情報入力フォーム
- `src/components/RequirementsList.tsx` - 構成要件リスト
- `src/components/ComplianceResults.tsx` - 充足性判定結果
- `e2e/analyze.spec.ts` - E2Eテスト

**実装方針**:

1. **shadcn/ui導入**: `npx shadcn-ui@latest init`でセットアップ
2. **必要なコンポーネント**: Button, Card, Input, Textarea, Badge, Dialog
3. **Tailwind CSS**: レスポンシブデザイン対応
4. **状態管理**: React hooks（useState, useEffect）
5. **API呼び出し**: fetch APIでNext.js API Routesを呼び出し

**主要ページの概要**:

**トップページ（src/app/page.tsx）**:

- プロジェクト概要の表示
- `/analyze`への導線

**分析ページ（src/app/analyze/page.tsx）**:

- 特許情報入力フォーム
- リアルタイム分析実行
- 結果表示エリア
- JSONダウンロード機能

**分析ページ（src/app/analyze/page.tsx）**:

```typescript
'use client';

import { useState } from 'react';
import { PatentInputForm } from '@/components/PatentInputForm';
import { RequirementsList } from '@/components/RequirementsList';
import { ComplianceResults } from '@/components/ComplianceResults';
import type { AnalysisResult } from '@/types/analysis';

export default function AnalyzePage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAnalyze = async (data: {
    patentNumber: string;
    claimText: string;
    companyName: string;
    productName: string;
  }) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const analysisResult = await response.json();
      setResult(analysisResult);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">特許侵害調査システム</h1>
      <PatentInputForm onSubmit={handleAnalyze} isLoading={isLoading} />
      {result && (
        <div className="mt-8 space-y-6">
          <RequirementsList requirements={result.requirements} />
          <ComplianceResults results={result.complianceResults} />
        </div>
      )}
    </div>
  );
}
```

**入力フォームコンポーネント（src/components/PatentInputForm.tsx）**:

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

interface PatentInputFormProps {
  onSubmit: (data: {
    patentNumber: string;
    claimText: string;
    companyName: string;
    productName: string;
  }) => void;
  isLoading: boolean;
}

export function PatentInputForm({ onSubmit, isLoading }: PatentInputFormProps) {
  const [formData, setFormData] = useState({
    patentNumber: '',
    claimText: '',
    companyName: '',
    productName: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="patentNumber">特許番号</label>
        <Input
          id="patentNumber"
          value={formData.patentNumber}
          onChange={(e) => setFormData({ ...formData, patentNumber: e.target.value })}
          placeholder="例: 06195960"
          required
        />
      </div>
      <div>
        <label htmlFor="claimText">請求項1</label>
        <Textarea
          id="claimText"
          value={formData.claimText}
          onChange={(e) => setFormData({ ...formData, claimText: e.target.value })}
          rows={8}
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="companyName">企業名</label>
          <Input
            id="companyName"
            value={formData.companyName}
            onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
            placeholder="例: TeamViewer"
            required
          />
        </div>
        <div>
          <label htmlFor="productName">製品名</label>
          <Input
            id="productName"
            value={formData.productName}
            onChange={(e) => setFormData({ ...formData, productName: e.target.value })}
            placeholder="例: TeamViewer Assist AR"
            required
          />
        </div>
      </div>
      <Button type="submit" disabled={isLoading}>
        {isLoading ? '分析中...' : '分析開始'}
      </Button>
    </form>
  );
}
```

**APIルート（src/app/api/analyze/route.ts）**:

```typescript
import { NextRequest, NextResponse } from "next/server";
import { extractRequirements } from "@/lib/requirements";
import { checkCompliance } from "@/lib/compliance";

export async function POST(request: NextRequest) {
  try {
    const { patentNumber, claimText, companyName, productName } = await request.json();

    // 構成要件抽出
    const requirements = await extractRequirements(patentNumber, claimText);

    // 充足性判定
    const complianceResults = await Promise.all(
      requirements.map((req) => checkCompliance(req, productName, companyName))
    );

    // 総合判定
    const compliantCount = complianceResults.filter((r) => r.compliance === "○").length;
    const totalCount = requirements.length;

    return NextResponse.json({
      patentNumber,
      companyName,
      productName,
      timestamp: new Date().toISOString(),
      requirements,
      complianceResults,
      summary: {
        totalRequirements: totalCount,
        compliantRequirements: compliantCount,
        complianceRate: (compliantCount / totalCount) * 100,
        infringementPossibility: compliantCount === totalCount ? "○" : "×",
      },
    });
  } catch (error) {
    console.error("Analysis error:", error);
    return NextResponse.json({ error: "Analysis failed" }, { status: 500 });
  }
}
```

**E2Eテスト（e2e/analyze.spec.ts）**:

```typescript
import { test, expect } from "@playwright/test";

test.describe("Patent Analysis Flow", () => {
  test("should complete full analysis workflow", async ({ page }) => {
    // ページに移動
    await page.goto("/analyze");

    // タイトルを確認
    await expect(page.locator("h1")).toContainText("特許侵害調査システム");

    // フォームに入力
    await page.fill("#patentNumber", "06195960");
    await page.fill("#claimText", "サーバーと、クライアント端末と、を含むシステムであって...");
    await page.fill("#companyName", "TeamViewer");
    await page.fill("#productName", "TeamViewer Assist AR");

    // 分析開始
    await page.click('button[type="submit"]');

    // ローディング状態を確認
    await expect(page.locator('button[type="submit"]')).toContainText("分析中");

    // 結果が表示されるまで待機
    await expect(page.locator("text=構成要件")).toBeVisible({ timeout: 30000 });

    // 構成要件が表示されることを確認
    await expect(page.locator("text=構成要件A")).toBeVisible();

    // 充足性判定結果が表示されることを確認
    await expect(page.locator("text=充足性判定")).toBeVisible();
  });

  test("should validate required fields", async ({ page }) => {
    await page.goto("/analyze");

    // 空のまま送信
    await page.click('button[type="submit"]');

    // HTML5のバリデーションが動作することを確認
    const patentNumberInput = page.locator("#patentNumber");
    await expect(patentNumberInput).toHaveAttribute("required", "");
  });
});
```

### Day 10: テストと修正

**作業内容**:

1. 実際の特許データでテスト
2. バグ修正と調整
3. ドキュメント作成

**成果物**:

- テスト結果レポート
- README.md
- setup.md

---

## Week 3: 検証と最適化（3日間）

### Day 11-12: 精度検証

**作業内容**:

1. サンプル特許データで検証（オプティムの特許5件程度）
2. 人間の判断との比較
3. プロンプトの調整と改善

**検証データ**:

- 特許06195960（遠隔指示システム）
- 特許05148670（固有アドレスによる電化製品設定）
- 特許06077068（拡張現実システム）
- 特許04895405（レピュテーションベースセキュリティ）

**検証指標**:
| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 構成要件抽出精度 | 90%以上 | 人間が抽出した構成要件と比較 |
| 充足性判定精度 | 80%以上 | 人間の判断と一致率 |
| 処理時間 | 5分/件以下 | 実測 |

### Day 13: ドキュメント整備とデモ準備

**作業内容**:

1. READMEの完成
2. セットアップガイドの作成
3. デモ用スクリプトの準備
4. Phase 1完成レポートの作成

**成果物**:

- 完成したPhase 1システム
- ドキュメント一式
- デモ用資料
- 精度検証レポート

---

## 技術仕様

### API利用

**OpenAI API**:

- モデル: gpt-3.5-turbo
- トークン制限: 2000 tokens/request
- Temperature: 0.3（一貫性重視）
- 推定コスト: $0.02〜1/月（10件分析時）

**Web検索**:

- 優先順位1: Perplexity API（無料枠: 100req/日）
- 優先順位2: SerpAPI（無料枠: 100検索/月）
- フォールバック: axios + Cheerio（Node.js用スクレイピング）

### データ形式

**入力データ**:

```json
{
  "patentNumber": "06195960",
  "claimText": "請求項1の全文...",
  "companyName": "TeamViewer",
  "productName": "TeamViewer Assist AR"
}
```

**出力データ**:

```json
{
  "patentNumber": "06195960",
  "companyName": "TeamViewer",
  "productName": "TeamViewer Assist AR",
  "timestamp": "2025-10-13T12:00:00",
  "requirements": [
    {
      "id": "1",
      "description": "構成要件A: ..."
    }
  ],
  "complianceResults": [
    {
      "requirementId": "1",
      "requirement": "構成要件A: ...",
      "compliance": "○",
      "reason": "製品は該当機能を実装している",
      "evidence": "公式ドキュメントに記載あり",
      "urls": ["https://example.com"]
    }
  ],
  "summary": {
    "totalRequirements": 5,
    "compliantRequirements": 5,
    "complianceRate": 100.0,
    "infringementPossibility": "○"
  }
}
```

---

## マイルストーン

| マイルストーン                 | 期限   | 成果物                           |
| ------------------------------ | ------ | -------------------------------- |
| **M1: プロジェクト初期化完了** | Day 2  | プロジェクト構造、プロンプト設計 |
| **M2: コアモジュール完成**     | Day 5  | 構成要件抽出、Web検索機能        |
| **M3: 充足性判定機能完成**     | Day 7  | 充足性判定モジュール             |
| **M4: UI完成**                 | Day 9  | Next.jsアプリ                    |
| **M5: 検証完了**               | Day 12 | 精度検証レポート                 |
| **M6: Phase 1完成**            | Day 13 | 完成システム + ドキュメント      |

---

## リスクと対策

| リスク                     | 影響度 | 対策                             |
| -------------------------- | ------ | -------------------------------- |
| OpenAI API制限・コスト超過 | 中     | キャッシング実装、トークン数削減 |
| Web検索API無料枠超過       | 中     | フォールバック実装、キャッシング |
| 構成要件抽出精度不足       | 高     | プロンプト改善、few-shot例追加   |
| 充足性判定精度不足         | 高     | プロンプト改善、検索結果の質向上 |
| 処理時間超過（5分/件）     | 低     | 並列処理、キャッシング           |

---

## 次のステップ

Phase 1完成後:

1. Phase 2（売上推定の自動化）の開発開始
2. Phase 1の改善点をフィードバック
3. Phase 2へのデータ連携設計

---

## 関連資料

- [PoC開発計画](./poc-development-plan.md) - PoC全体の計画
- [特許侵害調査ワークフロー](./patent-workflow.md) - 自動化対象のワークフロー
