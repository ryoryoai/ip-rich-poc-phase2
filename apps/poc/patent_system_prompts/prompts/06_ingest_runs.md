# 06 実装プロンプト: ingest_runs と処理の可観測性を足す

取り込み・解析を運用できるように、ingest_runs を実装してください。

## 要件
- ingest/parse の開始・終了・結果（成功/失敗）を ingest_runs に記録
- detail_json に、処理件数や例外メッセージ（短く）を残す
- 例外が起きても run レコードは finished_at まで残る

## ログ
- run_id をログに含める（構造化ログ推奨）

## CLI
- `python -m app.cli runs list` で直近の runs を表示
- `python -m app.cli runs show <run_id>` で detail_json を表示
