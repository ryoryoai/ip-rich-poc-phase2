# 02 実装プロンプト: リポジトリ骨組みを作る

既存の空リポジトリに、以下を追加してください。

## 追加するもの
- FastAPI アプリ（app/main.py）
- 設定（Pydantic Settings 推奨）: app/core/config.py
- DB接続: app/db/session.py
- SQLAlchemyモデル: app/db/models.py
- Alembic マイグレーションの初期セット
- Typer CLI: app/cli.py
- ログ設定: app/core/logging.py

## 期待する動作
- `GET /healthz` が 200 を返す
- `alembic upgrade head` が通る
- `.env.example` を用意し、必要な変数を列挙する

## 注意
- 依存パッケージは requirements.txt か pyproject.toml のどちらか一方に統一
- READMEにローカル手順を書く
