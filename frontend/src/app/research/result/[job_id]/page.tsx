"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  getJobStatus,
  getJobResults,
  type JobStatusResponse,
  type JobResultsResponse,
  type StageResult,
} from "@/lib/api";
import { parseResults } from "@/lib/parse-results";
import type { ParsedResults } from "@/lib/analysis-types";
import { CaseSummaryCard } from "@/components/analysis/case-summary-card";
import { ClaimDecisionCard } from "@/components/analysis/claim-decision-card";
import { ClaimElementsTable } from "@/components/analysis/claim-elements-table";
import { AssessmentHeatmap } from "@/components/analysis/assessment-heatmap";
import { InvestigationTasks } from "@/components/analysis/investigation-tasks";

function RawStageCard({ result }: { result: StageResult }) {
  const value = `stage-${result.stage}`;
  return (
    <AccordionItem value={value} className="border-none">
      <Card className="mb-2">
        <AccordionTrigger className="px-6 py-3 hover:no-underline">
          <div className="flex flex-1 items-center justify-between gap-4">
            <span className="text-sm font-medium">{result.stage}</span>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              {result.llm_model && <span>{result.llm_model}</span>}
              {result.latency_ms && <span>{result.latency_ms}ms</span>}
              {result.tokens_input !== null && result.tokens_output !== null && (
                <span>{result.tokens_input + result.tokens_output} tok</span>
              )}
            </div>
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <CardContent className="pt-0">
            <pre className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-64">
              {JSON.stringify(result.output_data, null, 2)}
            </pre>
          </CardContent>
        </AccordionContent>
      </Card>
    </AccordionItem>
  );
}

export default function JobResultPage() {
  const params = useParams();
  const jobId = params.job_id as string;

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [rawResults, setRawResults] = useState<JobResultsResponse | null>(null);
  const [parsed, setParsed] = useState<ParsedResults | null>(null);
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
        setRawResults(resultsData);
        setParsed(parseResults(resultsData.results));
      } catch (err) {
        setError(err instanceof Error ? err.message : "結果の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [jobId]);

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <div className="mb-6">
        <Link href="/research/list" className="text-blue-600 hover:text-blue-800 text-sm">
          &larr; 分析履歴一覧
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">分析結果</h1>

      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-muted-foreground">読み込み中...</p>
        </div>
      )}

      {error && (
        <Alert variant="destructive" className="mb-8">
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 1. 分析概要カード */}
      {job && (
        <Card className="mb-6">
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
                <p className={job.status === "completed" ? "text-green-600" : job.status === "failed" ? "text-red-600" : "text-yellow-600"}>
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
            {job.claim_nos && (
              <div className="mt-3">
                <p className="text-sm text-muted-foreground">
                  対象請求項: {job.claim_nos.join(", ")}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {parsed && (
        <>
          {/* 2. ケースサマリーカード */}
          {parsed.caseSummary && (
            <div className="mb-6">
              <CaseSummaryCard summary={parsed.caseSummary} />
            </div>
          )}

          {/* 3. 請求項判定グリッド */}
          {parsed.claims.length > 0 && parsed.claims.some((c) => c.decision) && (
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-4">請求項判定</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {parsed.claims
                  .filter((c) => c.decision)
                  .map((c) => (
                    <ClaimDecisionCard key={c.claim_no} decision={c.decision!} />
                  ))}
              </div>
            </div>
          )}

          {/* 4. 請求項別タブ */}
          {parsed.claims.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-4">請求項別詳細</h2>
              <Tabs defaultValue={String(parsed.claims[0].claim_no)}>
                <TabsList>
                  {parsed.claims.map((c) => (
                    <TabsTrigger key={c.claim_no} value={String(c.claim_no)}>
                      請求項 {c.claim_no}
                    </TabsTrigger>
                  ))}
                </TabsList>
                {parsed.claims.map((c) => (
                  <TabsContent key={c.claim_no} value={String(c.claim_no)} className="space-y-4 mt-4">
                    {/* 要素テーブル */}
                    {c.elements?.elements && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">構成要素 (Stage 10)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ClaimElementsTable elements={c.elements.elements} />
                        </CardContent>
                      </Card>
                    )}

                    {/* 充足判定テーブル */}
                    {c.assessment?.assessments && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">充足判定 (Stage 13)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <AssessmentHeatmap assessments={c.assessment.assessments} />
                        </CardContent>
                      </Card>
                    )}

                    {/* 判定詳細 */}
                    {c.decision && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">判定詳細 (Stage 14)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm mb-2">
                            <span className="font-medium">判定:</span>{" "}
                            {c.decision.decision} (確信度: {(c.decision.confidence * 100).toFixed(0)}%)
                          </p>
                          <p className="text-sm text-muted-foreground">{c.decision.rationale}</p>
                          {c.decision.open_items && c.decision.open_items.length > 0 && (
                            <div className="mt-2">
                              <p className="text-sm font-medium">未解決事項:</p>
                              <ul className="list-disc list-inside text-sm text-muted-foreground">
                                {c.decision.open_items.map((item, i) => (
                                  <li key={i}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}
                  </TabsContent>
                ))}
              </Tabs>
            </div>
          )}

          {/* 5. 調査タスク一覧 */}
          {parsed.investigationTasks?.tasks && parsed.investigationTasks.tasks.length > 0 && (
            <div className="mb-6">
              <InvestigationTasks tasks={parsed.investigationTasks.tasks} />
            </div>
          )}
        </>
      )}

      {/* 6. 生データアコーディオン */}
      {rawResults && rawResults.results.length > 0 && (
        <div className="mb-6">
          <Accordion type="single" collapsible>
            <AccordionItem value="raw-data">
              <AccordionTrigger className="text-sm font-medium">
                生データ ({rawResults.results.length} ステージ)
              </AccordionTrigger>
              <AccordionContent>
                <Accordion type="multiple">
                  {rawResults.results.map((result, index) => (
                    <RawStageCard key={index} result={result} />
                  ))}
                </Accordion>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      )}

      {rawResults && rawResults.results.length === 0 && !loading && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">結果がありません</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
