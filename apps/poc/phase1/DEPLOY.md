# Vercelへのデプロイ手順（CLIのみ）

## 前提条件
- Vercelアカウント（無料プランでOK）
- Node.js / npm がインストール済み

## デプロイ手順（CLI）

### 1. Vercel CLIのインストール

```bash
npm install -g vercel
```

### 2. プロジェクトのデプロイ

```bash
cd apps/poc/phase1
vercel # 環境によっては npx vercel
```

初回は以下の質問に答えます：
- Set up and deploy? → Yes
- Which scope? → あなたのアカウントを選択
- Link to existing project? → No（新規の場合）
- Project name → `your-project-name`（任意）
- Directory → `./`
- Override settings? → No

### 3. 環境変数の設定（CLI）

必要に応じて、Basic認証などの環境変数を CLI から追加します。

例（必要に応じて追加）：
- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`
- `SKIP_AUTH`（本番では必ず `false`）

```bash
# Basic認証の設定
vercel env add BASIC_AUTH_USERNAME production
vercel env add BASIC_AUTH_PASSWORD production

# 任意設定
vercel env add SKIP_AUTH production
```

### 4. 再デプロイ（CLI）

環境変数を設定・更新した場合は再デプロイします：

```bash
vercel --prod
```

## 動作確認

デプロイ後、以下のURLにアクセス：
```
https://your-app.vercel.app
```
Basic認証を設定した場合は、ダイアログでユーザー名とパスワードを入力してください。

## トラブルシューティング（CLI中心）

### 関数のタイムアウト調整
`vercel.json` の `maxDuration` を調整（最大300秒）：
```json
{
  "functions": {
    "src/app/api/*/route.ts": {
      "maxDuration": 300
    }
  }
}
```

## セキュリティ上の注意
1. Basic認証のパスワードは強固なものを使用（12文字以上、英数字と記号）
2. 認証情報をリポジトリにコミットしない（`.env.local` は `.gitignore` に含める）
3. 本番で `SKIP_AUTH` は使用しない

## デプロイ後の確認事項
- [ ] Basic認証が正常に動作する（設定した場合）
- [ ] トップページが表示される
- [ ] 「侵害調査を開始」ボタンが機能する

## サポート
- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)