#!/bin/bash

# 失敗したジョブをリトライするスクリプト
# 特定のジョブIDを指定してステータスをpendingに戻す

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
NC='\033[0m' # No Color

echo "=========================================="
echo "🔁 失敗ジョブリトライ"
echo "=========================================="
echo ""

# JOB_IDを引数から取得
if [ -z "$1" ]; then
    echo -e "${RED}❌ エラー: ジョブIDを指定してください${NC}"
    echo ""
    echo "使用方法: $0 <JOB_ID>"
    echo "例: $0 93aac077-392d-4041-9f41-7dd25a917b66"
    exit 1
fi

JOB_ID=$1

echo "対象ジョブID: $JOB_ID"
echo "API URL: ${API_URL}"
echo ""

echo -e "${YELLOW}📝 ジョブをpendingステータスにリセット中...${NC}"

# curlでPATCHリクエストを送信（本来はAPIエンドポイントがあればそれを使う）
# 今はSupabase MCPまたは直接SQLで対応が必要

echo -e "${YELLOW}⚠️  注意: 現在手動でデータベースを更新する必要があります${NC}"
echo ""
echo "以下のSQLをSupabaseで実行してください:"
echo ""
echo -e "${BLUE}UPDATE production.analysis_jobs${NC}"
echo -e "${BLUE}SET status = 'pending',${NC}"
echo -e "${BLUE}    progress = 0,${NC}"
echo -e "${BLUE}    started_at = NULL,${NC}"
echo -e "${BLUE}    finished_at = NULL,${NC}"
echo -e "${BLUE}    error_message = NULL,${NC}"
echo -e "${BLUE}    research_results = NULL${NC}"
echo -e "${BLUE}WHERE id = '${JOB_ID}';${NC}"
echo ""

echo "SQLを実行後、以下のコマンドでCronジョブを実行してください:"
echo ""
echo -e "${GREEN}./scripts/trigger-cron.sh${NC}"
echo ""
echo "または待機してスケジュール実行（15分ごと）を待つこともできます。"