"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getJobList, type JobListItem } from "@/lib/api";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "border-yellow-200 text-yellow-700 bg-yellow-50",
    researching: "border-blue-200 text-blue-700 bg-blue-50",
    analyzing: "border-purple-200 text-purple-700 bg-purple-50",
    completed: "border-green-200 text-green-700 bg-green-50",
    failed: "border-red-200 text-red-700 bg-red-50",
  };

  return (
    <Badge
      variant="outline"
      className={colors[status] || "border-gray-200 text-gray-700 bg-gray-50"}
    >
      {status}
    </Badge>
  );
}

export default function JobListPage() {
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;

  useEffect(() => {
    async function fetchJobs() {
      setLoading(true);
      try {
        const result = await getJobList(page, perPage);
        setJobs(result.jobs);
        setTotal(result.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "ジョブ一覧の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [page]);

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">分析履歴一覧</h1>
        <Button asChild>
          <Link href="/research">新規分析を開始</Link>
        </Button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-muted-foreground">読み込み中…</p>
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="mb-8">
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && !error && jobs.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">分析履歴がありません</p>
            <Link href="/research" className="text-blue-600 hover:text-blue-800 mt-2 inline-block">
              新規分析を開始
            </Link>
          </CardContent>
        </Card>
      )}

      {!loading && !error && jobs.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>分析ジョブ一覧</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {jobs.map((job) => (
                  <Link
                    key={job.id}
                    href={job.status === "completed" ? `/research/result/${job.id}` : `/research/status/${job.id}`}
                    className="block"
                  >
                    <div className="border rounded-lg p-4 hover:bg-muted/50 transition-colors">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{job.patent_id}</p>
                          <p className="text-sm text-muted-foreground">
                            パイプライン: {job.pipeline}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            作成: {new Date(job.created_at).toLocaleString("ja-JP")}
                          </p>
                        </div>
                        <div className="text-right">
                          <StatusBadge status={job.status} />
                          {job.infringement_score !== null && (
                            <p className="text-sm mt-2">
                              スコア: {job.infringement_score.toFixed(1)}%
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                前へ
              </Button>
              <span className="flex items-center px-4">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
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
