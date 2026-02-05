"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getJobStatus, retryJob, type JobStatusResponse } from "@/lib/api";

export default function JobStatusPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.job_id as string;

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    async function fetchStatus() {
      try {
        const result = await getJobStatus(jobId);
        setJob(result);
        setError(null);

        // Redirect to result page if completed
        if (result.status === "completed") {
          router.push(`/research/result/${jobId}`);
        }

        // Stop polling if completed or failed
        if (result.status === "completed" || result.status === "failed") {
          clearInterval(intervalId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "ステータスの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }

    fetchStatus();
    intervalId = setInterval(fetchStatus, 5000); // Poll every 5 seconds

    return () => clearInterval(intervalId);
  }, [jobId, router]);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await retryJob(jobId);
      setJob((prev) => prev ? { ...prev, status: "pending" } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "リトライに失敗しました");
    } finally {
      setRetrying(false);
    }
  };

  const statusLabels: Record<string, string> = {
    pending: "待機中",
    researching: "リサーチ中",
    analyzing: "分析中",
    completed: "完了",
    failed: "失敗",
  };

  const statusColors: Record<string, string> = {
    pending: "text-yellow-600",
    researching: "text-blue-600",
    analyzing: "text-purple-600",
    completed: "text-green-600",
    failed: "text-red-600",
  };

  return (
    <div className="container mx-auto p-8 max-w-3xl">
      <div className="mb-6">
        <Link href="/research/list" className="text-blue-600 hover:text-blue-800 text-sm">
          ← 分析履歴一覧
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">分析ステータス</h1>

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

      {job && (
        <Card>
          <CardHeader>
            <CardTitle>ジョブ詳細</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">ジョブID</p>
                <p className="font-mono text-sm">{job.job_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">ステータス</p>
                <p className={`font-medium ${statusColors[job.status]}`}>
                  {statusLabels[job.status] || job.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">特許番号</p>
                <p>{job.patent_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">パイプライン</p>
                <p>{job.pipeline}</p>
              </div>
              {job.current_stage && (
                <div className="col-span-2">
                  <p className="text-sm text-muted-foreground">現在のステージ</p>
                  <p>{job.current_stage}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">作成日時</p>
                <p className="text-sm">{new Date(job.created_at).toLocaleString("ja-JP")}</p>
              </div>
              {job.started_at && (
                <div>
                  <p className="text-sm text-muted-foreground">開始日時</p>
                  <p className="text-sm">{new Date(job.started_at).toLocaleString("ja-JP")}</p>
                </div>
              )}
            </div>

            {job.error_message && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{job.error_message}</p>
              </div>
            )}

            {(job.status === "pending" || job.status === "researching" || job.status === "analyzing") && (
              <div className="mt-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-muted-foreground">処理中…</p>
              </div>
            )}

            {job.status === "failed" && (
              <div className="mt-6 flex justify-center">
                <Button onClick={handleRetry} disabled={retrying}>
                  {retrying ? "リトライ中…" : "リトライ"}
                </Button>
              </div>
            )}

            {job.status === "completed" && (
              <div className="mt-6 flex justify-center">
                <Button asChild>
                  <Link href={`/research/result/${jobId}`}>結果を見る</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
