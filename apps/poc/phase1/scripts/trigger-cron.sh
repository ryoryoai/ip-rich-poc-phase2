#!/bin/bash

# Cronジョブ手動実行スクリプト
# /api/cron/check-and-do エンドポイントを手動で実行

# 設定
API_URL="https://ip-rich-poc-phase1.vercel.app"
# API_URL="http://localhost:3001"  # ローカルテスト用

# Basic認証設定
USERNAME="patent"
PASSWORD="data1234"

# Cron Secret
CRON_SECRET="cron-secret-key-phase1-batch-processing"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🤖 Cronジョブ手動実行"
echo "=========================================="
echo "API URL: ${API_URL}"
echo ""

echo -e "${YELLOW}📡 Cronエンドポイントを呼び出し中...${NC}"

# Cronエンドポイント呼び出し
response=$(curl -s -X GET \
  -u "${USERNAME}:${PASSWORD}" \
  -H "X-Cron-Secret: ${CRON_SECRET}" \
  "${API_URL}/api/cron/check-and-do")

# HTTPステータスコードを取得
http_status=$(curl -s -o /dev/null -w "%{http_code}" -X GET \
  -u "${USERNAME}:${PASSWORD}" \
  -H "X-Cron-Secret: ${CRON_SECRET}" \
  "${API_URL}/api/cron/check-and-do")

echo ""

if [ "$http_status" = "200" ]; then
    echo -e "${GREEN}✅ Cronジョブ実行成功${NC}"
    echo ""
    echo "📊 実行結果:"

    # JSONをパース（jqがインストールされている場合）
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi

    echo ""

    # 統計情報を表示
    if command -v jq &> /dev/null; then
        checked=$(echo "$response" | jq -r '.checked // 0')
        completed=$(echo "$response" | jq -r '.completed // 0')
        failed=$(echo "$response" | jq -r '.failed // 0')
        started=$(echo "$response" | jq -r '.started // 0')
        current_running=$(echo "$response" | jq -r '.currentRunning // 0')

        echo "📈 統計:"
        echo "   チェックしたジョブ: ${checked}"
        echo "   完了したジョブ: ${completed}"
        echo "   失敗したジョブ: ${failed}"
        echo "   新規開始ジョブ: ${started}"
        echo "   現在実行中: ${current_running}"
    fi
else
    echo -e "${RED}❌ Cronジョブ実行失敗 (HTTP ${http_status})${NC}"
    echo "Response: ${response}"
fi

echo ""
echo "=========================================="
echo ""
echo "📌 次のステップ:"
echo "1. ジョブ一覧を確認: ${API_URL}/research/list"
echo "2. 数分待ってから再度実行して進捗を確認"
echo "3. GitHub Actions で自動実行（15分ごと）"