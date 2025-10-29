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
        <div className="flex justify-center gap-4">
          <Link
            href="/analyze"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
          >
            🚀 侵害調査を開始
          </Link>
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

        {/* 現状と課題を追加 */}
        <div className="mt-16 space-y-8">
          <div className="bg-orange-50 border-2 border-orange-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-orange-900">⚠️ 現在の実装状況と課題</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">✅ 実装済み機能</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>OpenAI O4 Mini Deep Research APIとの統合</li>
                  <li>特許番号のみでの自動分析機能</li>
                  <li>非同期処理とポーリングメカニズム（最大3分）</li>
                  <li>詳細な進行状況のログ出力</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2 text-red-700">🚨 現在の課題</h3>
                <div className="bg-red-100 p-3 rounded-lg">
                  <p className="font-medium text-red-900">OpenAI Tier 1のレート制限エラー</p>
                  <code className="block mt-2 text-xs bg-white p-2 rounded text-red-800">
                    Rate limit reached for o4-mini-deep-research<br />
                    Limit: 200,000 TPM (Tier 1)<br />
                    Required: ~31,000 tokens per request
                  </code>
                  <p className="mt-2 text-sm text-gray-700">
                    特許調査には大量のトークンが必要なため、現在のTier 1では処理できません
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-green-900">📈 Next Steps</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">1. OpenAI Tierアップグレード（最優先）</h3>
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-2 text-left">Tier</th>
                      <th className="border p-2 text-left">TPM制限</th>
                      <th className="border p-2 text-left">必要条件</th>
                      <th className="border p-2 text-left">状態</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border p-2">Tier 1（現在）</td>
                      <td className="border p-2">200,000</td>
                      <td className="border p-2">$5支払い済み</td>
                      <td className="border p-2">❌ 不足</td>
                    </tr>
                    <tr>
                      <td className="border p-2">Tier 2</td>
                      <td className="border p-2">450,000</td>
                      <td className="border p-2">$50支払い + 7日経過</td>
                      <td className="border p-2">△ 最低限</td>
                    </tr>
                    <tr className="bg-green-100">
                      <td className="border p-2 font-bold">Tier 3（推奨）</td>
                      <td className="border p-2 font-bold">2,000,000</td>
                      <td className="border p-2 font-bold">$100支払い + 7日経過</td>
                      <td className="border p-2 font-bold">⭐ 推奨</td>
                    </tr>
                  </tbody>
                </table>
                <p className="mt-2 text-xs">
                  参考: <a href="https://platform.openai.com/docs/guides/rate-limits#usage-tiers"
                    className="text-blue-600 underline" target="_blank" rel="noopener noreferrer">
                    OpenAI Usage Tiers Documentation
                  </a>
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. 短期的な回避策</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>通常のGPT-4oモデルへの一時的な切り替え</li>
                  <li>プロンプトの最適化によるトークン使用量の削減</li>
                  <li>キャッシュ機能の実装（同じ特許の再検索防止）</li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">3. 中長期的な改善</h3>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>バッチ処理対応（複数特許の並列処理）</li>
                  <li>段階的な情報取得（必要最小限から開始）</li>
                  <li>Claude APIとの併用による負荷分散</li>
                </ul>
              </div>
            </div>
          </div>

        </div>
      </div>
    </main>
  );
}
