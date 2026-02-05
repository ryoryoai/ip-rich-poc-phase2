# Deep Research Service

特許情報取得のためのDeep Research APIをラップする外部サービス。Vercelの300秒タイムアウト制限を回避するため、長時間実行処理を非同期化し、Webhook経由で結果を返却します。

## 概要

- **実行時間**: 5-15分（OpenAI Deep Research API使用時）
- **アーキテクチャ**: Express + TypeScript
- **デプロイ先**: Render.com（無料枠、15分タイムアウト対応）
- **ローカルポート**: 3002

:::caution Phase1 legacy
Phase1のNext.jsアプリは削除済みで、Phase2では現在このサービスを利用していません。再利用する場合はPhase2側のWebhook受信/API設計に合わせて統合してください。
:::

## 機能

- 🔍 特許情報の非同期取得（Deep Research）
 - 🔄 Webhook送信機能（結果返却）
- 🎭 モック/実APIモード切り替え
- ⏱️ 長時間処理対応（最大15分）

## セットアップ

### 1. 依存関係のインストール

```bash
cd apps/deep-research-service
npm install
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして設定:

```bash
cp .env.example .env
```

```.env
# モード切り替え
USE_MOCK=true                  # true: モックモード（3秒待機）, false: 実APIモード

# ポート
PORT=3002

# Tavily API（実APIモード時のみ必要）
TAVILY_API_KEY=tvly-xxxxx
```

### 3. 開発サーバーの起動

```bash
npm run dev
```

http://localhost:3002/health で動作確認可能

## API エンドポイント

### `GET /health`

ヘルスチェック

**レスポンス**:
```json
{
  "status": "ok",
  "service": "deep-research-service"
}
```

### `POST /research/start`

特許情報取得を非同期で開始

**リクエスト**:
```json
{
  "job_id": "uuid-xxxx-xxxx-xxxx",
  "webhook_url": "https://your-app.com/api/webhook/research",
  "query": "JP06195960",
  "patent_mode": true,
  "next_js_api_url": "https://your-app.com"
}
```

**レスポンス** (即座に返却):
```json
{
  "status": "accepted",
  "job_id": "uuid-xxxx-xxxx-xxxx",
  "message": "Research started in background"
}
```

**Webhook送信（処理完了後）**:
```json
{
  "job_id": "uuid-xxxx-xxxx-xxxx",
  "status": "completed",
  "patent_info": {
    "patentNumber": "JP06195960",
    "patentTitle": "特許発明の名称",
    "claim1": "請求項1の内容",
    "assignee": "権利者名",
    "potentialInfringers": [
      {
        "company": "企業名",
        "product": "製品名",
        "probability": "高"
      }
    ]
  }
}
```

## モード切り替え

### モックモード（`USE_MOCK=true`）

- 3秒待機後、固定のモックデータを返す
- ローカル開発・テスト用
- 外部API呼び出しなし

**モックデータ**:
```javascript
{
  patentNumber: "入力された特許番号",
  patentTitle: "モック特許発明",
  claim1: "これはモックの請求項1の内容です。",
  assignee: "モック株式会社",
  potentialInfringers: [
    { company: "サンプル企業A", product: "サンプル製品X", probability: "高" },
    { company: "サンプル企業B", product: "サンプル製品Y", probability: "中" }
  ]
}
```

### 実APIモード（`USE_MOCK=false`）

- OpenAI Deep Research APIを呼び出し
- 実際の特許情報を取得（5-15分）
- Tavily APIキー必須

※ Phase2への統合は未実装です。再利用する場合はWebhook受信や認証設計を合わせてください。

## 開発コマンド

```bash
npm run dev         # 開発サーバー起動（ts-node-dev）
npm run build       # TypeScriptビルド
npm start           # プロダクションサーバー起動
```

## ローカル開発でのWebhook受信

ローカル環境でWebhookをテストする場合は、受信側APIをngrokで公開します。

### 手順

1. ngrokをインストールして認証
2. 受信側のポートを公開（例: `ngrok http 8000`）
3. `/research/start` の `webhook_url` にngrok URLを設定
4. Deep Research Serviceを起動
5. 受信側でWebhookが到達することを確認

## デプロイ（Render.com）

### 1. Render.comアカウント作成

https://render.com/ で無料アカウント作成

### 2. 新規Web Service作成

- **Build Command**: `npm install && npm run build`
- **Start Command**: `npm start`
- **Environment Variables**:
  ```
  USE_MOCK=false
  TAVILY_API_KEY=tvly-xxxxx
  PORT=3002
  ```

### 3. Next.js側の環境変数更新

Vercelの環境変数に追加:
```bash
DEEP_RESEARCH_SERVICE_URL=https://your-service.onrender.com
```

## トラブルシューティング

### Webhook送信エラー

- 受信側のWebhookエンドポイントがアクセス可能か確認
- ngrokが起動しているか確認（ローカル開発時）
- `webhook_url`が正しく設定されているか確認

### モックモードで結果が返らない

- Deep Research Serviceが起動しているか確認（http://localhost:3002/health）
- `USE_MOCK=true`が設定されているか確認
- ログを確認: `[Research]`または`[Patent Research]`で始まるログ

### 実APIモードでエラー

- `TAVILY_API_KEY`が設定されているか確認
- OpenAI APIキーが有効か確認

## ログ確認

```bash
# 開発サーバーのログ
npm run dev

# 以下のようなログが表示されます
[Research] Starting job xxxx for query: "JP06195960" (patent_mode: true)
[Patent Research] Job xxxx: Fetching patent info for "JP06195960"...
[Patent Research] Job xxxx: Patent research completed, sending webhook...
[Patent Research] Job xxxx: Webhook sent successfully
```

## 参考資料

- **ASIS.md**: 現状の実装シーケンス
- **TOBE.md**: 理想の実装計画（OpenAI Deep Research API統合）
