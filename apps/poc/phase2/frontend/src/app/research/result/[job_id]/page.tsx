"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getJobStatus, getJobResults, type JobStatusResponse, type JobResultsResponse, type StageResult } from "@/lib/api";

function StageResultCard({ result }: { result: StageResult }) {
  const value = `stage-${result.stage}`;

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value={value} className="border-none">
        <Card className="mb-4">
          <AccordionTrigger className="px-6 py-4 hover:no-underline">
            <div className="flex flex-1 items-center justify-between gap-4">
              <CardTitle className="text-base">{result.stage}</CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {result.llm_model && <span>{result.llm_model}</span>}
                {result.latency_ms && <span>{result.latency_ms}ms</span>}
                {result.tokens_input !== null && result.tokens_output !== null && (
                  <span>{result.tokens_input + result.tokens_output} tokens</span>
                )}
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <CardContent>
              <pre className="text-xs bg-muted p-4 rounded-md overflow-auto max-h-96">
                {JSON.stringify(result.output_data, null, 2)}
              </pre>
            </CardContent>
          </AccordionContent>
        </Card>
      </AccordionItem>
    </Accordion>
  );
}

export default function JobResultPage() {
  const params = useParams();
  const jobId = params.job_id as string;

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [results, setResults] = useState<JobResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [jobData, resultsData] = await Promise.all([
          getJobStatus(jobId),
          getJobResults(jobId),
        ]);
        setJob(jobData);
        setResults(resultsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "結果の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [jobId]);

  // Extract summary from case_summary stage if available
  const summaryResult = results?.results.find((r) => r.stage.includes("case_summary"));
  const summary = summaryResult?.output_data as Record<string, unknown> | undefined;

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="mb-6">
        <Link href="/research/list" className="text-blue-600 hover:text-blue-800 text-sm">
          ← 分析履歴一覧
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">分析結果</h1>

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
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>分析概要</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">特許番号</p>
                <p className="font-medium">{job.patent_id}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">パイプライン</p>
                <p>{job.pipeline}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">ステータス</p>
                <p className={job.status === "completed" ? "text-green-600" : "text-yellow-600"}>
                  {job.status}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">完了日時</p>
                <p className="text-sm">
                  {job.completed_at ? new Date(job.completed_at).toLocaleString("ja-JP") : "-"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {summary && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>サマリー</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none">
              {typeof summary === "object" && "summary" in summary && (
                <p>{String(summary.summary)}</p>
              )}
              {typeof summary === "object" && "recommendation" in summary && (
                <div className="mt-4">
                  <h4 className="font-medium">推奨事項</h4>
                  <p>{String(summary.recommendation)}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {results && results.results.length > 0 && (
        <div>
          <h2 className="text-xl font-bold mb-4">ステージ別結果</h2>
          {results.results.map((result, index) => (
            <StageResultCard key={index} result={result} />
          ))}
        </div>
      )}

      {results && results.results.length === 0 && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">結果がありません</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
