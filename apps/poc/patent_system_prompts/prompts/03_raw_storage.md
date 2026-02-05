# 03 実装プロンプト: Raw保管（不変ストレージ）を作る

Rawファイル（ZIP/XML等）を保存し、メタデータをDBに記録する機能を実装してください。

## 要件
- 入力: ローカルファイルパス（後でURL入力も追加できる構造にしてよい）
- 実装: `app/ingest/raw_storage.py`
- 保存先: まずはローカルディスク（例: /data/raw）でよい
- 物理パス（オブジェクトキー）設計:
  - source=local / acquired_date=YYYY-MM-DD / sha256[:2]/sha256 / original_name
  - 例: source=local/acquired_date=2026-02-04/ab/ab12.../foo.zip

## DB
- raw_files に記録
  - sha256 はユニーク制約
  - original_name, stored_path, acquired_at, metadata_json

## 冪等
- 既に同じ sha256 が存在すれば、保存と登録をスキップ（同じ id を返す）

## 追加
- CLI: `python -m app.cli ingest --path /path/to/dir` でディレクトリ配下を一括登録
- ログ: 取り込み件数、スキップ件数、失敗件数

## テスト
- 小さなダミーファイルを作って ingest し、二度目がスキップされること
