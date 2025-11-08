#!/bin/bash

set -e

echo "================================================"
echo "スキーマリセット & セットアップスクリプト"
echo "================================================"
echo ""
echo "⚠️  警告: 既存のデータは全て削除されます！"
echo ""
read -p "続行しますか? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "キャンセルしました。"
  exit 0
fi

echo ""
echo "環境変数を確認中..."
if [ -z "$DIRECT_URL" ]; then
  echo "❌ DIRECT_URL環境変数が設定されていません。"
  echo ""
  echo ".env.localファイルから読み込みます..."
  if [ -f .env.local ]; then
    set -a
    source .env.local
    set +a
    echo "✅ .env.localを読み込みました"
  else
    echo "❌ .env.localファイルが見つかりません。"
    exit 1
  fi
fi

if [ -z "$DIRECT_URL" ]; then
  echo "❌ DIRECT_URLが設定されていません。"
  echo ".env.localにDIRECT_URLを追加してください。"
  exit 1
fi

echo ""
echo "接続先（DIRECT_URL）: $DIRECT_URL"
echo ""

echo "SQLスクリプトを実行中（Prisma CLI使用）..."
cat prisma/migrations/setup_schemas.sql | npx prisma db execute --stdin --schema prisma/schema.prisma

echo ""
echo "✅ スキーマのセットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "1. DATABASE_URLの schema パラメータを確認"
echo "   - ローカル: ?schema=local"
echo "   - 本番: ?schema=production"
echo ""
echo "2. Prisma Clientを再生成"
echo "   npm run prisma:generate"
echo ""
