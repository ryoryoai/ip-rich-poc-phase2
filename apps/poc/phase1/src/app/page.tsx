import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-8 text-center">
          特許侵害調査システム - Phase 1 PoC
        </h1>
        <p className="text-center mb-8">
          特許の構成要件抽出と侵害可能性を自動判定するシステムです
        </p>
        

        {/* 現状と課題を追加 */}
        <div className="mt-16 space-y-8">
          <div className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-green-900">✅ 実装完了</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">🎉 Phase 1 PoC 完成</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>OpenAI O4 Mini Deep Research APIによる特許情報の自動取得</li>
                  <li>特許番号入力のみで侵害可能性のある製品を自動検出</li>
                  <li>非同期処理による長時間分析のサポート（最大15分）</li>
                  <li>Supabase + Prismaによるジョブ管理とデータ永続化</li>
                  <li>Webhook + ポーリングによる確実な結果取得</li>
                  <li>マークダウン形式での分析結果表示</li>
                  <li>Vercelへのデプロイ完了（productionスキーマ）</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-blue-700">💼 ビジネス的にできるようになったこと</h3>
                <div className="bg-blue-50 p-3 rounded-lg">
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    <li><strong>Deep Research侵害調査結果のデータベース管理</strong></li>
                    <li className="ml-6 text-xs">- 特許番号と請求項1を入力するだけで侵害製品調査を開始</li>
                    <li className="ml-6 text-xs">- 調査結果をデータベースに保存し、いつでも参照可能</li>
                    <li className="ml-6 text-xs">- 過去の調査履歴を一覧で確認・再利用できる</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-blue-900">🚀 Phase 2: iprich内での業務利用可能性検証</h2>
            <div className="space-y-4">
              <div className="bg-blue-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-blue-900">
                  🎯 目標: iprich内で業務利用可能性を検証可能な状態を目指す
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">1. 前提条件</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li className="text-green-700 font-semibold">OpenAI API契約（iprich）で7日経過後、$50課金済み</li>
                  <li className="text-green-700 font-semibold">Tier 2へアップグレード完了</li>
                  <li>TPM (Tokens Per Minute): 2,000,000 → 安定した分析実行が可能</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. 主要機能の実装</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li className="font-semibold text-blue-700">侵害製品の売上規模推定機能の追加</li>
                  <li className="ml-6 text-xs">- sample/被疑侵害製品の売上推定のプロンプト.txt を実装</li>
                  <li className="ml-6 text-xs">- 企業の財務情報・市場規模からの売上推定</li>
                  <li className="ml-6 text-xs">- 損害賠償額の概算計算</li>
                  <li className="font-semibold text-blue-700">侵害調査結果の構造化とDB保存</li>
                  <li className="ml-6 text-xs">- 製品ごとの充足性判定データを構造化</li>
                  <li className="ml-6 text-xs">- 検索・分析可能な形式でDBに保存</li>
                  <li className="ml-6 text-xs">- 過去の調査結果との比較分析を可能に</li>
                  <li>イレギュラー発生時の自動化（エラー時の通知・再実行）</li>
                  <li>ユーザー管理とマルチテナント対応</li>
                  <li>分析履歴の管理とダッシュボード</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border-2 border-purple-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-purple-900">🔮 Phase 3: iprich内での大規模利用検証</h2>
            <div className="space-y-4">
              <div className="bg-purple-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-purple-900">
                  🎯 目標: iprichで大規模利用可能か検証可能な状態を目指す
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">バッチ処理による大規模分析</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li><strong>複数特許の一括分析</strong> - バッチ実行による効率化</li>
                  <li>特許ポートフォリオ全体の侵害リスク評価</li>
                  <li>業界全体の侵害動向分析</li>
                  <li>スケジュール実行による定期監視</li>
                  <li>定期的な新製品監視とアラート機能</li>
                  <li>分析結果のエクスポート機能（Excel、PDF）</li>
                  <li className="font-semibold text-purple-700">J-PlatPatとの連携</li>
                  <li className="ml-6 text-xs">- 特許情報の自動取得</li>
                  <li className="ml-6 text-xs">- 請求項データの構造化</li>
                  <li className="ml-6 text-xs">- 特許ステータスの自動確認</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-orange-50 border-2 border-orange-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-orange-900">🌐 Phase 4: 外部公開に向けた大規模開発</h2>
            <div className="space-y-4">
              <div className="bg-orange-100 p-3 rounded-lg mb-4">
                <p className="text-sm font-semibold text-orange-900">
                  🎯 目標: 外部公開を目指して大規模開発を行う
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">エンタープライズ対応</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>マルチテナント・エンタープライズアーキテクチャ</li>
                  <li>高度なセキュリティとアクセス制御</li>
                  <li>APIエンドポイント化（外部システム連携）</li>
                  <li>SLA保証とサポート体制の構築</li>
                  <li>パフォーマンス最適化とスケーラビリティ向上</li>
                  <li>料金プラン設計と課金システム</li>
                  <li>ドキュメントとオンボーディング整備</li>
                </ul>
              </div>
            </div>
          </div>

        </div>
      </div>
      
        <div className="mt-16">
          <h2 className="text-xl font-bold mb-4 text-center">システムの使い方</h2>
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">📝 Step 1: 特許情報の入力</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li><strong>特許番号</strong>を入力（例: 07666636, US7666636）</li>
                <li><strong>請求項1の全文</strong>を入力</li>
                <li>この2つだけで分析開始！</li>
              </ul>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">🔍 Step 2: AI による自動調査（バックグラウンド実行）</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>OpenAI Deep ResearchがWeb検索で情報収集</li>
                <li>日本国内でサービス展開している外国企業の製品を調査</li>
                <li>請求項1の構成要件を満たす製品を検出</li>
                <li>最大15分の長時間分析をサポート</li>
              </ul>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">📊 Step 3: 結果の確認</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>各製品の構成要件充足性をマークダウンテーブルで表示</li>
                <li>充足判断（○/×）と根拠となるURL・公開情報を提示</li>
                <li>複数製品の分析結果を一覧で確認可能</li>
                <li>分析履歴はデータベースに保存され、いつでも参照可能</li>
              </ul>
            </div>
          </div>
      </div>
      <div className="flex justify-center gap-4">
          <Link
            href="/research"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
          >
            🚀 侵害調査を開始
          </Link>
        </div>
    </main>
  );
}
