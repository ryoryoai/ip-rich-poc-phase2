# 07 実装プロンプト: APIエンドポイントを完成させる

FastAPIのエンドポイントを実装してください。

## 必須
- GET /healthz
  - 200 {"status":"ok"}
- GET /v1/patents/resolve?input=...
  - input から doc_number/kind を推測して候補を返す
  - MVPでは「数字のみ→登録番号として照合」「JP1234567B2 形式→分解」程度でよい
- GET /v1/patents/{patent_id}/claims/1
  - patent_id は内部IDでも、(country, doc_number, kind) を連結したものでもよい
  - 404/422 を適切に返す

## 望ましい
- OpenAPIが読みやすい（response model を定義）
- 返却に source_raw_file_id を含める（監査性）
- APIレイヤでDBセッションの扱いを安全に

## テスト
- TestClient で resolve → claims/1 が取れるフローを通す
