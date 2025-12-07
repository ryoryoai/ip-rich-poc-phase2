#!/bin/bash

# テストデータ一括登録スクリプト
# Production環境の特許データをcurlで登録

# 設定
API_URL="https://ip-rich-poc-phase1.vercel.app"
# API_URL="http://localhost:3001"  # ローカルテスト用

# Basic認証設定
USERNAME="patent"
PASSWORD="datas1234"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🚀 特許侵害調査テストデータ登録"
echo "=========================================="
echo "API URL: ${API_URL}"
echo ""

# 特許データ配列
declare -a PATENTS=(
  # 特許番号7666636: 球技の挙動評価
  '{"patentNumber":"7666636","claimText":"身体運動に関する時系列データを入力とし、身体動作から身体動作に伴う物体の挙動の推定結果を出力するように学習されたモデルを用いて、対象者の身体運動に関する時系列データから前記対象者の身体動作に伴う物体の挙動を推定する推定部と、推定した物体の挙動と実際の物体の挙動との誤差に基づき、前記対象者を評価する評価部とを含み、前記対象者の身体運動に関する時系列データは、前記対象者の対戦相手から見た前記対象者の動作に関連する時系列データであり、前記評価部は、推定した前記物体の挙動と、実際の前記物体の挙動との乖離が大きいほど高い評価を算出し、前記対象者が行う運動は対戦型の球技であり、前記物体は球技で使われる球である","priority":8}'

  # 特許番号7492160: （技術内容は要確認）
  '{"patentNumber":"7492160","claimText":"請求項1の内容をここに記載（要確認）","priority":5}'

  # 特許番号5398392: 空調機器制御装置
  '{"patentNumber":"5398392","claimText":"温度センサーと湿度センサーを含む環境測定部と、前記環境測定部からの測定データに基づいて空調機器を制御する制御部と、ユーザーの位置情報を取得する位置情報取得部と、前記位置情報に基づいて前記制御部の動作を変更する動作変更部とを備え、前記動作変更部は、ユーザーが設定した地理的範囲から離れたことを検知した場合に前記空調機器を省エネルギーモードに切り替える","priority":7}'
)

# 関数: APIにジョブを登録
register_job() {
  local patent_data=$1
  local patent_number=$(echo $patent_data | grep -o '"patentNumber":"[^"]*' | cut -d'"' -f4)

  echo -e "${YELLOW}📝 特許番号 ${patent_number} を登録中...${NC}"

  response=$(curl -s -X POST \
    -u "${USERNAME}:${PASSWORD}" \
    -H "Content-Type: application/json" \
    -d "${patent_data}" \
    "${API_URL}/api/patent-search/schedule")

  # レスポンスの確認
  if echo "$response" | grep -q "job_id"; then
    job_id=$(echo $response | grep -o '"job_id":"[^"]*' | cut -d'"' -f4)
    status=$(echo $response | grep -o '"status":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✅ 成功: 特許番号 ${patent_number}${NC}"
    echo "   Job ID: ${job_id}"
    echo "   Status: ${status}"
    echo ""
  else
    echo -e "${RED}❌ 失敗: 特許番号 ${patent_number}${NC}"
    echo "   Response: ${response}"
    echo ""
  fi
}

# メイン処理
echo "📊 登録する特許数: ${#PATENTS[@]}"
echo ""

for patent in "${PATENTS[@]}"; do
  register_job "$patent"
  # API負荷を考慮して少し待機
  sleep 1
done

echo "=========================================="
echo "✨ テストデータ登録完了"
echo "=========================================="
echo ""
echo "📌 次のステップ:"
echo "1. 一覧画面で確認: ${API_URL}/research/list"
echo "2. Cronジョブ実行: ./trigger-cron.sh"
echo "3. ステータス確認: ${API_URL}/research/status/{job_id}"