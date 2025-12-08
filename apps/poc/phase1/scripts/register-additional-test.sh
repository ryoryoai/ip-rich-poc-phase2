#!/bin/bash

# 追加テストデータ登録スクリプト
# 同時実行制限のテスト用

# 設定
API_URL="https://ip-rich-poc-phase1.vercel.app"
# API_URL="http://localhost:3001"  # ローカルテスト用

# Basic認証設定
USERNAME="patent"
PASSWORD="data1234"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🧪 同時実行制限テスト用データ登録"
echo "=========================================="
echo "API URL: ${API_URL}"
echo ""

# 3つの追加テストジョブを登録
echo -e "${YELLOW}📝 追加テストデータ（高優先度）を登録中...${NC}"
RESPONSE=$(curl -s -X POST \
  -u "${USERNAME}:${PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"patentNumber":"TEST-HIGH","claimText":"テスト用高優先度特許の請求項1","priority":10}' \
  "${API_URL}/api/patent-search/schedule")

if echo "$RESPONSE" | grep -q "job_id"; then
  echo -e "${GREEN}✅ 成功: 高優先度テスト${NC}"
  echo "$RESPONSE" | jq -r '"   Job ID: \(.job_id)\n   Status: \(.status)"'
else
  echo -e "${RED}❌ 失敗: 高優先度テスト${NC}"
fi

echo ""
echo -e "${YELLOW}📝 追加テストデータ（中優先度）を登録中...${NC}"
RESPONSE=$(curl -s -X POST \
  -u "${USERNAME}:${PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"patentNumber":"TEST-MID","claimText":"テスト用中優先度特許の請求項1","priority":6}' \
  "${API_URL}/api/patent-search/schedule")

if echo "$RESPONSE" | grep -q "job_id"; then
  echo -e "${GREEN}✅ 成功: 中優先度テスト${NC}"
  echo "$RESPONSE" | jq -r '"   Job ID: \(.job_id)\n   Status: \(.status)"'
else
  echo -e "${RED}❌ 失敗: 中優先度テスト${NC}"
fi

echo ""
echo -e "${YELLOW}📝 追加テストデータ（低優先度）を登録中...${NC}"
RESPONSE=$(curl -s -X POST \
  -u "${USERNAME}:${PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"patentNumber":"TEST-LOW","claimText":"テスト用低優先度特許の請求項1","priority":3}' \
  "${API_URL}/api/patent-search/schedule")

if echo "$RESPONSE" | grep -q "job_id"; then
  echo -e "${GREEN}✅ 成功: 低優先度テスト${NC}"
  echo "$RESPONSE" | jq -r '"   Job ID: \(.job_id)\n   Status: \(.status)"'
else
  echo -e "${RED}❌ 失敗: 低優先度テスト${NC}"
fi

echo ""
echo "=========================================="
echo "📌 Cronを実行して同時実行制限を確認:"
echo "  ./scripts/trigger-cron.sh"
echo ""
echo "期待される動作:"
echo "  - 現在実行中: 1件"
echo "  - 新規開始: 1件のみ（最大2件の制限）"
echo "  - 待機: 2件"
echo "=========================================="