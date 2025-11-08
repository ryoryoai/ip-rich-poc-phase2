# Phase 1: 特許侵害調査自動化システム (PoC)

## 概要

特許の構成要件を抽出し、指定された製品の侵害可能性を自動判定するシステムのPoC実装です。

## 機能

- 📝 特許請求項から構成要件を自動抽出（Claude 3.5 Sonnet）
- 🔍 Web検索による製品仕様の自動収集（Tavily API）
- ⚖️ 各構成要件の充足性を自動判定
- 📊 侵害可能性の総合評価とレポート生成
- 💾 結果のJSON形式エクスポート

## 技術スタック

- **フロントエンド**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui
- **LLM**: Claude 3.5 Sonnet（Anthropic）または OpenAI GPT
- **Web検索**: Tavily API（無料枠: 1000検索/月）
- **データベース**: Supabase（PostgreSQL）- 無料枠500MB
- **ORM**: Prisma 6.19.0
- **アーキテクチャ**: 依存性注入によるプロバイダー切り替え可能

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env.local.example` を `.env.local` にコピーして、必要なAPIキーを設定します。

```bash
cp .env.local.example .env.local
```

### 必要なAPIキー

#### Claude API（推奨）
- **取得先**: https://console.anthropic.com/
- **無料枠**: 新規アカウントで$5クレジット
- **設定**:
  ```
  LLM_PROVIDER=claude
  ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
  ```

#### または OpenAI API
- **取得先**: https://platform.openai.com/
- **設定**:
  ```
  LLM_PROVIDER=openai
  OPENAI_API_KEY=sk-xxxxx
  ```

#### Tavily API（Web検索）
- **取得先**: https://tavily.com/
- **無料枠**: 1000検索/月
- **設定**:
  ```
  SEARCH_PROVIDER=tavily
  TAVILY_API_KEY=tvly-xxxxx
  ```

#### Supabase（データベース） + Prisma ORM
- **取得先**: https://supabase.com/
- **無料枠**: 500MB データベース + 1GB ストレージ
- **セットアップ手順**:
  1. Supabaseアカウント作成（無料）
  2. 新規プロジェクト作成（リージョン: Northeast Asia推奨）
  3. **Project Settings** → **API** から以下を取得:
     - Project URL
     - anon public key
     - service_role key
  4. **Project Settings** → **Database** → **Connection string** から:
     - Connection pooling URL (Transaction modeではなくSession mode)
  5. `.env.local`に設定（パスワードはURLエンコード必須）:
     ```bash
     # Supabase API
     NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
     NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

     # Prisma (特殊文字は%エンコード: / → %2F, @ → %40)
     # schema=local または schema=production でスキーマを切り替え
     # ローカル開発:
     DATABASE_URL="postgresql://postgres:postgres@localhost:54322/postgres?schema=local"
     # 本番環境:
     DATABASE_URL="postgresql://postgres.xxxxx:[PASSWORD]@aws-x-xx-xxxx-x.pooler.supabase.com:6543/postgres?schema=production&pgbouncer=true&connection_limit=1"
     ```
  6. スキーマをセットアップ（初回のみ）:
     ```bash
     # 方法1: スクリプト実行（推奨）
     cd apps/poc/phase1
     ./scripts/reset-and-setup-schemas.sh

     # 方法2: 手動実行
     # schemaパラメータを除去したURLでマイグレーション実行
     psql "postgresql://postgres:postgres@localhost:54322/postgres" -f prisma/migrations/setup_schemas.sql
     ```

     ⚠️ **注意**: このスクリプトは既存のテーブルを全て削除します！

  7. Prisma Clientを生成:
     ```bash
     npm run prisma:generate
     ```

### 環境の切り替え

`.env.local`の`DATABASE_URL`の`schema`パラメータを変更:

```bash
# ローカル開発環境
DATABASE_URL="postgresql://postgres:postgres@localhost:54322/postgres?schema=local"

# 本番環境
DATABASE_URL="postgresql://postgres.[ref]:[password]@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres?schema=production"
```

スキーマを変更した後は必ずPrisma Clientを再生成:
```bash
npm run prisma:generate
```

### 3. データベース接続テスト

#### オプション1: Supabase JS SDK（レガシー）

```bash
node scripts/test-supabase-connection.mjs
```

#### オプション2: Prisma ORM（推奨）

開発サーバーを起動後:
```bash
# GET: ジョブ一覧・ステータス別集計
curl http://localhost:3001/api/test-prisma

# POST: テストジョブ作成
curl -X POST http://localhost:3001/api/test-prisma
```

または、Prisma Studioでデータベースを視覚的に確認:
```bash
npm run prisma:studio
# http://localhost:5555 で起動
```

### 4. Deep Research Service環境変数の設定

Deep Research ServiceでWebhook経由で特許情報を取得する場合、以下の環境変数を設定します。

```bash
# apps/deep-research-service/.env
USE_MOCK=true                                      # モックモード（本番はfalse）
PORT=3002
TAVILY_API_KEY=tvly-xxxxx                          # 実APIモード時のみ必要
```

`.env.local`にDeep Research Service関連の設定を追加:

```bash
# Deep Research Service
DEEP_RESEARCH_SERVICE_URL=http://localhost:3002    # ローカル開発時
NEXT_PUBLIC_APP_URL=http://localhost:3001          # Next.jsアプリのURL

# ngrok使用時は以下のように変更（後述）
# NEXT_PUBLIC_APP_URL=https://xxxx-xx-xx-xxx-xxx.ngrok-free.app
```

### 5. 開発サーバーの起動

#### Next.js開発サーバー（port 3001）

```bash
npm run dev
```

http://localhost:3001 でアクセス可能

#### Deep Research Service（port 3002）

別ターミナルで起動:

```bash
cd ../../deep-research-service
npm install  # 初回のみ
npm run dev
```

http://localhost:3002/health で動作確認可能

### 6. ngrokでWebhook受信を有効化（任意）

ローカル開発環境でWebhookを受信するには、ngrokを使ってNext.jsを外部公開します。

**詳細な設定手順は `NGROK_SETUP.md` を参照してください。**

#### クイックスタート

```bash
# ngrokインストール（初回のみ）
brew install ngrok

# 認証設定（初回のみ）
ngrok config add-authtoken YOUR_AUTH_TOKEN

# トンネル開始
ngrok http 3001
```

#### 環境変数の更新

`.env.local`:
```bash
NEXT_PUBLIC_APP_URL=https://xxxx-xx-xx-xxx-xxx.ngrok-free.app
```

#### 疎通確認

スマホで以下にアクセス:
```
https://xxxx-xx-xx-xxx-xxx.ngrok-free.app/api/ngrok/health
```

## 使い方

1. トップページの「分析を開始」ボタンをクリック
2. 以下の情報を入力:
   - **特許番号**: 例: 06195960
   - **請求項1**: 特許の請求項1の全文
   - **企業名**: 調査対象の企業名（例: TeamViewer）
   - **製品名**: 調査対象の製品名（例: TeamViewer Assist AR）
3. 「分析開始」ボタンをクリック
4. 分析結果が表示されます（約30秒〜1分）
5. 結果をJSONでダウンロード可能

## プロバイダーの切り替え

環境変数でプロバイダーを切り替え可能:

- `LLM_PROVIDER`: openai | claude
- `SEARCH_PROVIDER`: dummy | tavily
- `STORAGE_PROVIDER`: local

## 開発コマンド

```bash
npm run dev                              # 開発サーバー起動
npm run build                            # プロダクションビルド
npm run start                            # プロダクションサーバー起動
npm run lint                             # Lintチェック
npm run type-check                       # 型チェック
node scripts/test-supabase-connection.mjs  # Supabase接続テスト
```

## コスト見積もり

### Claude API（無料枠$5）
- 構成要件抽出: 約1,000トークン/件
- 充足性判定: 約2,000トークン/件
- **特許10件分析可能**（無料枠内）

### Tavily API（無料枠1000検索/月）
- 製品検索: 3-5検索/分析
- **月200-300件の分析可能**

## トラブルシューティング

### API Keyエラー
- `.env.local`ファイルが正しく設定されているか確認
- APIキーが有効か確認

### データベース接続エラー

**Supabase JS SDK**:
- `node scripts/test-supabase-connection.mjs` でテスト実行
- `.env.local`のSupabase API設定を確認

**Prisma ORM**:
- `npm run prisma:studio` でPrisma Studioが起動するか確認
- `.env.local`の`DATABASE_URL`を確認（パスワードがURLエンコードされているか）
- 特殊文字のエンコード例: `/` → `%2F`, `@` → `%40`

### 検索結果が空
- Tavily APIキーが設定されているか確認
- 無料枠の制限（1000検索/月）を超えていないか確認

### 分析が遅い
- Claude APIの応答に時間がかかる場合があります（通常30秒〜1分）
- ネットワーク接続を確認

## 注意事項

- このシステムは概念実証（PoC）版です
- 分析結果は参考情報として利用してください
- 実際の特許侵害判定には専門家の確認が必要です

## ライセンス

Private