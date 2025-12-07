# GitHub Actions Secrets設定ガイド

## 必要なSecrets

GitHub リポジトリの Settings → Secrets and variables → Actions で以下のSecretsを設定してください：

### 1. CRON_SECRET_KEY
**説明**: Cronエンドポイントの認証用シークレットキー
**推奨値**: `cron-secret-key-phase1-batch-processing` または強力なランダム文字列
**環境変数と同じ値を設定**

### 2. BASIC_AUTH_USERNAME
**説明**: Basic認証のユーザー名
**現在の値**: `patent`

### 3. BASIC_AUTH_PASSWORD
**説明**: Basic認証のパスワード
**現在の値**: `datas1234`

## 設定手順

1. GitHubリポジトリの **Settings** タブを開く
2. 左メニューから **Secrets and variables** → **Actions** を選択
3. **New repository secret** ボタンをクリック
4. 各Secretを追加：
   - Name: `CRON_SECRET_KEY`
   - Secret: `cron-secret-key-phase1-batch-processing`
5. 同様に `BASIC_AUTH_USERNAME` と `BASIC_AUTH_PASSWORD` も追加

## 動作確認

### 手動実行テスト
1. **Actions** タブを開く
2. **Patent Search Batch Processing** ワークフローを選択
3. **Run workflow** ボタンをクリック
4. **Dry run mode** にチェックを入れてテスト実行
5. 成功したら、チェックを外して本番実行

### スケジュール実行
- **22:00 JST**: 高優先度ジョブ（優先度8-10）
- **23:00 JST**: 中優先度ジョブ（優先度4-7）
- **00:00 JST**: 低優先度ジョブ（優先度0-3）

## トラブルシューティング

### エラー: Unauthorized (401)
- `CRON_SECRET_KEY` が正しく設定されているか確認
- `BASIC_AUTH_USERNAME` と `BASIC_AUTH_PASSWORD` が正しいか確認

### エラー: Not Found (404)
- デプロイメントURLが正しいか確認
- Vercelにデプロイが成功しているか確認

### ログの確認方法
```bash
# Vercel CLIでログ確認
vercel logs ip-rich-poc-phase1.vercel.app

# GitHub Actionsのログ
# Actions → 該当のワークフロー実行 → ジョブをクリック
```

## 本番環境の環境変数（Vercel）

Vercelダッシュボードで以下の環境変数も設定が必要です：

1. `CRON_SECRET_KEY`
2. `BASIC_AUTH_USERNAME`
3. `BASIC_AUTH_PASSWORD`
4. `DATABASE_URL`
5. `DIRECT_URL`
6. `OPENAI_API_KEY`
7. `ANTHROPIC_API_KEY` (オプション)
8. `TAVILY_API_KEY` (オプション)

設定方法：
```bash
vercel env add CRON_SECRET_KEY production
# プロンプトで値を入力
```

または、Vercelダッシュボード → Settings → Environment Variables から設定