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
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            分析を開始
          </Link>
        </div>
        <div className="mt-16">
          <h2 className="text-2xl font-bold mb-4">機能</h2>
          <ul className="list-disc list-inside space-y-2">
            <li>請求項1から構成要件を自動抽出</li>
            <li>Web検索で製品仕様を自動収集（Tavily API）</li>
            <li>Claude 3.5 Sonnetで充足性を自動判定</li>
            <li>結果をJSON形式で保存</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
