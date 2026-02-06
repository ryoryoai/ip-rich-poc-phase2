"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getCases, type CaseItem } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  draft: "下書き",
  exploring: "調査中",
  reviewing: "レビュー中",
  confirmed: "確定",
  archived: "アーカイブ",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "text-gray-600 bg-gray-100",
  exploring: "text-blue-600 bg-blue-100",
  reviewing: "text-yellow-600 bg-yellow-100",
  confirmed: "text-green-600 bg-green-100",
  archived: "text-muted-foreground bg-muted",
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const perPage = 20;

  useEffect(() => {
    async function fetchCases() {
      setLoading(true);
      try {
        const data = await getCases({ page, per_page: perPage });
        setCases(data.cases);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "案件一覧の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    fetchCases();
  }, [page]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">案件管理</h1>
        <Link href="/cases/new">
          <Button>新規案件作成</Button>
        </Link>
      </div>

      {error && (
        <div className="text-red-600 mb-4 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-muted-foreground text-sm">読み込み中...</p>
        </div>
      ) : cases.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">案件がありません</p>
            <Link href="/cases/new" className="text-blue-600 text-sm mt-2 inline-block">
              最初の案件を作成する
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            {cases.map((c) => (
              <Link key={c.id} href={`/cases/${c.id}`}>
                <Card className="hover:border-blue-300 transition-colors cursor-pointer">
                  <CardHeader className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{c.title}</CardTitle>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${STATUS_COLORS[c.status] || "text-gray-600 bg-gray-100"}`}
                      >
                        {STATUS_LABELS[c.status] || c.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="py-2 px-4">
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      {c.description && (
                        <span className="truncate max-w-md">{c.description}</span>
                      )}
                      <span className="ml-auto">
                        {new Date(c.created_at).toLocaleDateString("ja-JP")}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                前へ
              </Button>
              <span className="text-sm text-muted-foreground">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                次へ
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
