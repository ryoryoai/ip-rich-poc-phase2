import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "特許侵害調査システム - Phase 1 PoC",
  description: "特許の構成要件抽出と侵害可能性の自動判定",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
