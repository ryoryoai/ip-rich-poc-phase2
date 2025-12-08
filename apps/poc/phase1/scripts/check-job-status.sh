#!/bin/bash

# ジョブステータス確認スクリプト
# 登録されたジョブの一覧とステータスを確認

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
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=========================================="
echo "📊 ジョブステータス確認"
echo "=========================================="
echo "API URL: ${API_URL}"
echo ""

# オプション引数でステータスフィルタリング
STATUS_FILTER=""
if [ ! -z "$1" ]; then
    STATUS_FILTER="?status=$1"
    echo -e "${CYAN}フィルター: status = $1${NC}"
    echo ""
fi

# ジョブ一覧を取得
echo -e "${YELLOW}📋 ジョブ一覧を取得中...${NC}"
response=$(curl -s -u "${USERNAME}:${PASSWORD}" \
    "${API_URL}/api/analyze/list${STATUS_FILTER}")

# jqがインストールされているか確認
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}jq がインストールされていません。生データを表示します。${NC}"
    echo "$response"
    exit 0
fi

# ジョブ数を取得
total=$(echo "$response" | jq -r '.total // 0')

echo ""
echo -e "${GREEN}📊 合計ジョブ数: ${total}${NC}"
echo ""

# ステータスごとにカウント
pending_count=$(echo "$response" | jq '[.jobs[] | select(.status == "pending")] | length')
researching_count=$(echo "$response" | jq '[.jobs[] | select(.status == "researching")] | length')
completed_count=$(echo "$response" | jq '[.jobs[] | select(.status == "completed")] | length')
failed_count=$(echo "$response" | jq '[.jobs[] | select(.status == "failed")] | length')

echo "📈 ステータス別集計:"
echo -e "   ${YELLOW}⏳ pending (待機中):${NC} ${pending_count}"
echo -e "   ${BLUE}🔄 researching (調査中):${NC} ${researching_count}"
echo -e "   ${GREEN}✅ completed (完了):${NC} ${completed_count}"
echo -e "   ${RED}❌ failed (失敗):${NC} ${failed_count}"
echo ""

# ジョブ詳細を表示
echo "📋 ジョブ詳細:"
echo "----------------------------------------"

# 各ジョブの情報を表示
echo "$response" | jq -r '.jobs[] |
    "Job ID: \(.job_id)\n" +
    "  特許番号: \(.patent_number // "N/A")\n" +
    "  ステータス: \(.status)\n" +
    "  優先度: \(.priority // 5)\n" +
    "  進捗: \(.progress)%\n" +
    "  作成日時: \(.created_at)\n" +
    if .started_at then "  開始日時: \(.started_at)\n" else "" end +
    if .finished_at then "  完了日時: \(.finished_at)\n" else "" end +
    if .error_message then "  エラー: \(.error_message)\n" else "" end +
    "----------------------------------------"'

echo ""
echo "📌 使用方法:"
echo "  全ジョブ表示: ./check-job-status.sh"
echo "  待機中のみ: ./check-job-status.sh pending"
echo "  調査中のみ: ./check-job-status.sh researching"
echo "  完了のみ: ./check-job-status.sh completed"
echo "  失敗のみ: ./check-job-status.sh failed"
echo ""
echo "🔗 Webで確認: ${API_URL}/research/list"