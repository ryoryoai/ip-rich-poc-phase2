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
                <h3 className="font-semibold mb-2 text-blue-700">📊 動作確認済み項目</h3>
                <div className="bg-blue-50 p-3 rounded-lg">
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    <li>Basic認証（patent:data1234）の動作確認</li>
                    <li>データベース接続とスキーマ分離（local/production）</li>
                    <li>環境変数の正しい設定と管理</li>
                    <li>ビルドとデプロイの成功</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-blue-900">🚀 Phase 2に向けて</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">1. 実用化に向けた課題</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li className="text-orange-700 font-semibold">OpenAI APIのレート制限対策（Tier 2以上へのアップグレード）</li>
                  <li>分析精度の向上（プロンプトエンジニアリング）</li>
                  <li>コスト最適化（キャッシュ戦略、必要最小限のトークン使用）</li>
                  <li>エラーハンドリングとリトライ戦略の強化</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. 機能拡張計画</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>複数特許の一括分析機能</li>
                  <li>侵害製品の売上規模推定</li>
                  <li>損害賠償額の概算計算</li>
                  <li>定期的な新製品監視とアラート機能</li>
                  <li>分析結果のエクスポート機能（Excel、PDF）</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">3. システム改善</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>ユーザー管理とマルチテナント対応</li>
                  <li>分析履歴の管理とダッシュボード</li>
                  <li>APIエンドポイント化（外部システム連携）</li>
                  <li>パフォーマンス最適化とスケーラビリティ向上</li>
                </ul>
              </div>

              <div className="bg-yellow-50 p-3 rounded-lg mt-4">
                <p className="text-sm text-yellow-900">
                  <strong>💡 推奨事項:</strong> 本格運用前にOpenAI APIのTier 2以上へのアップグレードが必要です。
                  現在のTier 1（200,000 TPM）では、Deep Research APIの実行に制限があります。
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
      
        <div className="mt-16">
          <h2 className="text-xl font-bold mb-4 text-center">システムの特徴</h2>
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">🔍 Step 1: 特許情報取得</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>特許番号のみ入力でOK</li>
                <li>O4 Mini Deep Researchが特許情報を自動取得</li>
                <li>J-PlatPat、USPTO、Google Patentsから情報収集</li>
                <li>請求項1と特許権者を自動抽出</li>
              </ul>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">🎯 Step 2: 潜在的侵害製品の検出</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Deep Researchが関連製品を自動検出</li>
                <li>日本国内でサービス展開している外国企業を重点調査</li>
                <li>侵害可能性の高い製品をリストアップ</li>
              </ul>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-bold mb-2">⚖️ Step 3: 侵害調査分析</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>各構成要件の充足性を判定</li>
                <li>製品の仕様と特許請求項を詳細比較</li>
                <li>根拠となる公開情報を提示</li>
                <li>結果をJSON形式でエクスポート</li>
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
