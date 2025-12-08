#!/bin/bash

# Production Schema 初期化スクリプト
# ⚠️ 注意: このスクリプトは本番環境のデータを削除します

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo -e "${RED}⚠️  Production Schema 初期化${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}警告: このスクリプトは production schema の全データを削除します！${NC}"
echo ""

# 確認プロンプト
read -p "本当に実行しますか？ (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${BLUE}キャンセルしました。${NC}"
    exit 0
fi

# 二重確認
echo ""
echo -e "${RED}最終確認: production.analysis_jobs の全データが削除されます。${NC}"
read -p "本当によろしいですか？ 'DELETE ALL' と入力してください: " final_confirmation

if [ "$final_confirmation" != "DELETE ALL" ]; then
    echo -e "${BLUE}キャンセルしました。${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🔄 データベース初期化を開始します...${NC}"
echo ""

# 環境変数の読み込み
cd "$(dirname "$0")/.."

# 本番環境の環境変数を取得
if [ ! -f .env.production.local ]; then
    echo -e "${YELLOW}📥 Vercel から環境変数を取得中...${NC}"
    vercel env pull .env.production.local --environment production
fi

# データベースのクリーンアップ（Prisma経由）
echo -e "${YELLOW}🗑️  analysis_jobs テーブルのデータを削除中...${NC}"

# Node.jsスクリプトを使用してデータベースをクリア
node -e "
const { PrismaClient } = require('@prisma/client');
require('dotenv').config({ path: '.env.production.local' });

const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
});

async function clearDatabase() {
  try {
    // analysis_jobs テーブルの全データを削除
    const deleted = await prisma.analysis_jobs.deleteMany();
    console.log('✅ 削除完了: ' + deleted.count + ' 件のレコードを削除しました');
  } catch (error) {
    console.error('❌ エラー:', error.message);
    process.exit(1);
  } finally {
    await prisma.\$disconnect();
  }
}

clearDatabase();
"

echo ""
echo -e "${GREEN}✨ データベース初期化完了${NC}"
echo "=========================================="
echo ""
echo "📌 次のステップ:"
echo "1. テストデータを登録: ./scripts/register-test-data.sh"
echo "2. 一覧画面で確認: https://ip-rich-poc-phase1.vercel.app/research/list"