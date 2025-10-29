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
      </div>
    </main>
  );
}
