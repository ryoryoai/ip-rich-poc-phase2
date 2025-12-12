---
sidebar_position: 1
---

# IP Rich Tools ドキュメント

特許侵害調査を自動化するシステムのドキュメントサイトです。

## プロジェクト概要

IP Rich Toolsは、特許侵害調査プロセスを自動化し、効率化するためのシステムです。

### 主な機能（Phase 1 実装済み）

- **侵害調査の自動化**: OpenAI Deep Research APIを使用した自動分析
- **バッチ処理**: GitHub Actions Cronによる夜間実行
- **履歴管理**: 調査結果のデータベース保存と閲覧

### 技術スタック

- **フロントエンド**: Next.js 14 (App Router)
- **バックエンド**: Next.js API Routes
- **データベース**: Supabase PostgreSQL (Prisma)
- **AI**: OpenAI Deep Research API
- **ホスティング**: Vercel
- **CI/CD**: GitHub Actions

## ドキュメント構成

### アーキテクチャ

- [AWS Infrastructure Architecture](./architecture.md) - ドキュメントサイトのインフラ構成

### ワークフロー

- [特許侵害調査ワークフロー](./patent-workflow.md) - 自動化対象のワークフローと現行業務

### 開発計画

- [PoC開発計画 v1.1](./poc-development-plan-v1.1.md) - 現在の実装アーキテクチャ
- [Phase 1 実装計画](./phase1-implementation-plan.md) - 詳細な実装内容とAPI仕様

## クイックスタート

### ドキュメントサイト

```bash
cd docs-site
npm install
npm start  # http://localhost:1919
```

### Patent Analysis App

```bash
cd apps/poc/phase1
npm install
npm run dev  # http://localhost:3001
```

## 開発フェーズ

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1 | 侵害調査の自動化 | ✅ 完了 |
| Phase 2 | 業務利用可能性検証 | 🔄 進行中 |
| Phase 3 | J-PlatPat連携、侵害額推定 | 📋 計画中 |
| Phase 4 | ログイン機能、利用料管理 | 📋 計画中 |

## 関連リンク

- [GitHub Repository](https://github.com/fshmng09/ip-rich-tools)
- [Phase 1 アプリケーション](https://ip-rich-poc-phase1.vercel.app)
