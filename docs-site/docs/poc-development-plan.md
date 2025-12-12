---
sidebar_position: 4
---

# PoC開発計画（旧版）

:::warning このドキュメントは旧版です
このドキュメントは当初の計画書です。現在の実装については **[PoC開発計画 v1.1（実装完了版）](./poc-development-plan-v1.1.md)** を参照してください。
:::

## 変更履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| v1.0 | 2024年10月 | 初期計画（同期処理、Claude/OpenAI Chat API） |
| v1.1 | 2024年11月 | 非同期処理対応（OpenAI Deep Research API、GitHub Actions Cron） |

## v1.0からv1.1への主な変更点

| 項目 | v1.0（旧） | v1.1（現在） |
|------|-----------|-------------|
| **LLM** | Claude 3.5 Sonnet / GPT-4 | OpenAI Deep Research API |
| **処理方式** | 同期処理 | 非同期処理（Webhook） |
| **タイムアウト対策** | なし | background: true |
| **データベース** | ローカルJSON | Prisma + Supabase PostgreSQL |
| **バッチ処理** | なし | GitHub Actions Cron |
| **検索** | Tavily API | OpenAI Deep Research内蔵 |

---

## 最新のドキュメント

- **[PoC開発計画 v1.1（実装完了版）](./poc-development-plan-v1.1.md)** - 現在の実装
- **[Phase 1 実装計画](./phase1-implementation-plan.md)** - 詳細な実装内容
- **[特許侵害調査ワークフロー](./patent-workflow.md)** - 自動化対象のワークフロー
