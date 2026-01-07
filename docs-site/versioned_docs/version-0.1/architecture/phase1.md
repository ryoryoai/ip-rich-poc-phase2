---
sidebar_position: 1
sidebar_label: MVP用 コスト優先
---

# MVP用アーキテクチャ（コスト優先）

Phase 1 で実装した特許侵害調査自動化システムのアーキテクチャです。コスト効率を重視した構成になっています。

## システム構成図

```plantuml Phase 1 Architecture
skinparam backgroundColor #FFFFFF
skinparam componentStyle rectangle

actor "ユーザー" as user

rectangle "Vercel" #E5F5FF {
  rectangle "Next.js App Router" as nextjs {
    component "/research\n(UI)" as ui
    component "/api/analyze/*\n(API)" as api
    component "/api/cron/*\n(Cron)" as cron
    component "/api/webhook/*\n(Webhook)" as webhook
  }
}

rectangle "OpenAI" #FFF5E5 {
  component "Deep Research API\n(o4-mini)" as openai
}

rectangle "Supabase" #E5FFE5 {
  database "PostgreSQL\n(analysis_jobs)" as db
}

rectangle "GitHub Actions" #FFE5E5 {
  component "Cron Job\n(15分毎)" as ghcron
}

user --> ui : ブラウザアクセス
ui --> api : 分析リクエスト
api --> db : ジョブ作成
ghcron --> cron : 定期実行
cron --> db : pending取得
cron --> openai : Deep Research\n開始
openai --> webhook : 完了通知
webhook --> db : 結果保存
ui --> api : 結果取得
api --> db : 結果読込

note right of openai
  **Deep Research**
  ・Web検索内蔵
  ・非同期処理
  ・background: true
end note

note bottom of db
  **Prisma Schema**
  ・analysis_jobs
  ・ジョブステータス管理
  ・検索結果保存
end note
```

## コンポーネント詳細

### フロントエンド (Vercel)

| コンポーネント | 説明 |
|--------------|------|
| `/research` | 分析一覧・詳細表示UI |
| `/api/analyze/start` | 分析ジョブ開始 |
| `/api/analyze/status` | ジョブステータス確認 |
| `/api/analyze/result` | 分析結果取得 |
| `/api/analyze/list` | ジョブ一覧取得 |

### バッチ処理

| コンポーネント | 説明 |
|--------------|------|
| `/api/cron/check-and-do` | pendingジョブを取得しDeep Research開始 |
| GitHub Actions | 15分毎にcronエンドポイントを呼び出し |

### AI エンジン (OpenAI)

| 項目 | 値 |
|-----|-----|
| モデル | `o4-mini-deep-research-2025-06-26` |
| 処理方式 | 非同期 (`background: true`) |
| 完了通知 | Webhook |
| 特徴 | Web検索機能内蔵 |

### データベース (Supabase)

| テーブル | 説明 |
|---------|------|
| `analysis_jobs` | 分析ジョブの状態・結果を管理 |

**ジョブステータス遷移**:
```
pending → researching → completed
                     → failed
```

## データフロー

### 1. ジョブ登録

```
ユーザー → UI → /api/analyze/start → Supabase (status: pending)
```

### 2. バッチ処理開始

```
GitHub Actions → /api/cron/check-and-do → Supabase (pending取得)
                                        → OpenAI Deep Research (開始)
                                        → Supabase (status: researching)
```

### 3. 結果受信

```
OpenAI → /api/webhook/openai → Supabase (結果保存, status: completed)
```

### 4. 結果表示

```
ユーザー → UI → /api/analyze/result → Supabase → UI (結果表示)
```

## 認証

| 対象 | 方式 |
|-----|------|
| UI/API | Basic認証 |
| Cronエンドポイント | `X-Cron-Secret` ヘッダー |
| Webhook | OpenAI署名検証 |

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| フレームワーク | Next.js 14 (App Router) |
| 言語 | TypeScript |
| ORM | Prisma |
| データベース | PostgreSQL (Supabase) |
| AI | OpenAI Deep Research API |
| ホスティング | Vercel |
| CI/CD | GitHub Actions |
