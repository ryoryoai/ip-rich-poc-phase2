# Vercelへのデプロイ手順

## 前提条件
- Vercelアカウント（無料プランでOK）
- GitHubアカウント
- OpenAI APIキー（Tier 2以上推奨）

## デプロイ手順

### 1. Vercel CLIのインストール（オプション）

```bash
npm install -g vercel
```

### 2. プロジェクトのデプロイ

#### 方法A: Vercel CLIを使用（推奨）

```bash
cd apps/poc/phase1
vercel
```

初回は以下の質問に答えます：
- Set up and deploy? → Yes
- Which scope? → あなたのアカウントを選択
- Link to existing project? → No（新規の場合）
- Project name → `ip-patent-analyzer`（任意）
- Directory → `./`
- Override settings? → No

#### 方法B: GitHub連携

1. GitHubにリポジトリをプッシュ
2. [Vercel Dashboard](https://vercel.com/new)にアクセス
3. "Import Git Repository"を選択
4. GitHubリポジトリを選択
5. Root Directoryを`apps/poc/phase1`に設定
6. "Deploy"をクリック

### 3. 環境変数の設定

Vercel Dashboardで以下の環境変数を設定：

#### 必須の環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `BASIC_AUTH_USERNAME` | Basic認証のユーザー名 | `admin` |
| `BASIC_AUTH_PASSWORD` | Basic認証のパスワード | `your-secure-password` |
| `OPENAI_API_KEY` | OpenAI APIキー | `sk-proj-xxxxx` |
| `LLM_PROVIDER` | LLMプロバイダー | `openai` |
| `MODEL_NAME` | 使用するモデル | `o4-mini-deep-research-2025-06-26` |

#### オプションの環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|------------|
| `SKIP_AUTH` | Basic認証をスキップ | `false` |
| `ANTHROPIC_API_KEY` | Claude API（フォールバック用） | なし |
| `TAVILY_API_KEY` | Tavily Search API | なし |
| `SEARCH_PROVIDER` | 検索プロバイダー | `tavily` |

### 4. 環境変数の設定方法

#### Vercel Dashboard経由

1. Vercelダッシュボードでプロジェクトを開く
2. "Settings" → "Environment Variables"に移動
3. 各環境変数を追加：
   - Key: 変数名（例: `BASIC_AUTH_USERNAME`）
   - Value: 値（例: `admin`）
   - Environment: Production, Preview, Development（全て選択）
4. "Save"をクリック

#### Vercel CLI経由

```bash
# Basic認証の設定
vercel env add BASIC_AUTH_USERNAME production
vercel env add BASIC_AUTH_PASSWORD production

# OpenAI APIキーの設定
vercel env add OPENAI_API_KEY production

# その他の設定
vercel env add LLM_PROVIDER production
vercel env add MODEL_NAME production
```

### 5. 再デプロイ

環境変数を設定後、再デプロイが必要です：

```bash
vercel --prod
```

または、Vercel Dashboardから"Redeploy"をクリック

## Basic認証の動作確認

デプロイ後、以下のURLにアクセス：
```
https://your-app.vercel.app
```

Basic認証のダイアログが表示されたら、設定したユーザー名とパスワードを入力

## トラブルシューティング

### Basic認証が機能しない

1. 環境変数が正しく設定されているか確認
2. Vercel Dashboardで"Functions"タブを確認し、ミドルウェアがデプロイされているか確認

### APIタイムアウトエラー

`vercel.json`の`maxDuration`を調整（最大300秒）：
```json
{
  "functions": {
    "src/app/api/*/route.ts": {
      "maxDuration": 300
    }
  }
}
```

### OpenAI レート制限エラー

- OpenAIアカウントのTierを確認（Tier 2以上推奨）
- 環境変数`MODEL_NAME`を通常の`gpt-4o`に変更してテスト

## セキュリティ上の注意

1. **Basic認証のパスワードは強固なものを使用**
   - 最低12文字以上
   - 英数字と記号を組み合わせる

2. **APIキーの管理**
   - GitHubにAPIキーをコミットしない
   - `.env.local`ファイルは`.gitignore`に含める

3. **アクセス制限**
   - 必要に応じてVercelのFirewall機能でIPアドレス制限を追加

## デプロイ後の確認事項

- [ ] Basic認証が正常に動作する
- [ ] トップページが表示される
- [ ] 「侵害調査を開始」ボタンが機能する
- [ ] 環境変数が正しく読み込まれている

## よくある質問

### Q: 無料プランでデプロイできますか？
A: はい、Vercelの無料プランでデプロイ可能です。ただし、以下の制限があります：
- 月100GBの帯域幅
- 関数の実行時間は最大10秒（Proプランでは300秒）

### Q: カスタムドメインは設定できますか？
A: はい、Vercel Dashboardの"Domains"から設定可能です。

### Q: 複数環境（開発/本番）を分けることはできますか？
A: はい、ブランチごとに異なる環境変数を設定できます。

## サポート

問題が発生した場合は、以下を確認してください：
- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- GitHubのIssueで質問