import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AuthGate from "@/components/auth/auth-gate";
import AuthStatus from "@/components/auth/auth-status";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Phase2 - 特許データ検索",
  description: "日本特許の請求項データを検索・表示するシステム",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className={inter.className}>
        <AuthGate>
          <div className="min-h-screen bg-background">
            <header className="border-b">
              <div className="container mx-auto px-4 py-4 flex items-center justify-between gap-6">
                <h1 className="text-xl font-bold">Phase2 - 特許データシステム</h1>
                <div className="flex items-center gap-4">
                  <nav className="flex flex-wrap gap-4">
                    <a href="/" className="text-sm hover:underline">
                      請求項検索
                    </a>
                    <a href="/research" className="text-sm hover:underline">
                      侵害調査
                    </a>
                    <a href="/research/list" className="text-sm hover:underline">
                      分析履歴
                    </a>
                    <a href="/analysis" className="text-sm hover:underline">
                      パイプライン分析
                    </a>
                    <a href="/master/companies" className="text-sm hover:underline">
                      会社マスタ
                    </a>
                    <a href="/master/products" className="text-sm hover:underline">
                      製品マスタ
                    </a>
                    <a href="/master/keywords" className="text-sm hover:underline">
                      技術キーワード
                    </a>
                    <a href="/master/review" className="text-sm hover:underline">
                      レビュー
                    </a>
                    <a href="/jp-index" className="text-sm hover:underline">
                      JP Index
                    </a>
                    <a href="/jp-index/changes" className="text-sm hover:underline">
                      JP差分
                    </a>
                    <a href="/jp-index/ingest" className="text-sm hover:underline">
                      JP取込
                    </a>
                  </nav>
                  <AuthStatus />
                </div>
              </div>
            </header>
            <main className="container mx-auto px-4 py-8">{children}</main>
          </div>
        </AuthGate>
      </body>
    </html>
  );
}
