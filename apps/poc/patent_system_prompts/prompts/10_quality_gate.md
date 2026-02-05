# 10 実装プロンプト: 品質ゲート（静的解析・整形）

コードベースの品質を最低限そろえてください。

## 必須
- ruff（lint）
- black（format）
- mypy（型チェック）※厳しすぎる場合は段階的でよい
- pre-commit（任意だが推奨）

## CI（任意）
- GitHub Actions で lint + test

## 目的
- ingest/parse は壊れやすいので、CIで守る
