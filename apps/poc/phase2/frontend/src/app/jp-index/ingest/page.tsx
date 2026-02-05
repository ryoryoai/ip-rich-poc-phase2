"use client";

import { useEffect, useState } from "react";
import { Database, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getJpIndexIngestRuns, type JpIndexIngestRun } from "@/lib/api";

export default function JpIndexIngestPage() {
  const [runs, setRuns] = useState<JpIndexIngestRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getJpIndexIngestRuns(50);
      setRuns(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            取り込み監視
          </CardTitle>
          <CardDescription>
            JP Patent Index の取り込み履歴を表示します
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            最新 {runs.length} 件を表示
          </div>
          <Button onClick={fetchRuns} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            更新
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>取り込み履歴</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {runs.length === 0 && (
            <div className="text-sm text-muted-foreground">
              取り込み履歴がありません。
            </div>
          )}
          {runs.map((run) => (
            <div key={run.batch_id} className="border rounded-md p-4 space-y-1">
              <div className="font-semibold">
                {run.source} / {run.run_type} / {run.update_date || "更新日不明"}
              </div>
              <div className="text-sm text-muted-foreground">
                状態: {run.status} / 開始: {run.started_at || "不明"} / 終了:{" "}
                {run.finished_at || "不明"}
              </div>
              {run.counts && (
                <div className="text-sm">
                  取り込み件数: {run.counts.records ?? run.counts.ingested ?? "-"} / エラー:{" "}
                  {run.counts.errors ?? 0}
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
