"use client";

import { useState } from "react";
import { Play, Loader2, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  startAnalysis,
  getJobResults,
  type StartAnalysisRequest,
  type JobResultsResponse,
  type StageResult,
} from "@/lib/api";

type Pipeline = "A" | "B" | "C" | "full";

const PIPELINE_INFO: Record<Pipeline, { name: string; description: string }> = {
  A: { name: "Fetch/Normalize", description: "特許データの取得・正規化" },
  B: { name: "Discovery", description: "検索シード生成・候補ランキング" },
  C: { name: "Analyze", description: "請求項分解・侵害判定" },
  full: { name: "Full", description: "全パイプライン実行" },
};

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "failed":
      return <XCircle className="h-5 w-5 text-red-500" />;
    case "running":
      return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    default:
      return <AlertCircle className="h-5 w-5 text-gray-500" />;
  }
}

function StageResultCard({ result }: { result: StageResult }) {
  const value = `stage-${result.stage}`;

  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value={value} className="border-none">
        <Card>
          <AccordionTrigger className="px-6 py-4 hover:no-underline">
            <div className="flex flex-1 items-center justify-between gap-4">
              <CardTitle className="text-base">{result.stage}</CardTitle>
              <div className="text-sm text-muted-foreground">
                {result.llm_model && (
                  <span className="mr-4">Model: {result.llm_model}</span>
                )}
                {result.tokens_input && result.tokens_output && (
                  <span className="mr-4">
                    Tokens: {result.tokens_input} / {result.tokens_output}
                  </span>
                )}
                {result.latency_ms && <span>{result.latency_ms}ms</span>}
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            {result.output_data && (
              <CardContent>
                <pre className="bg-muted p-4 rounded-md overflow-auto text-xs max-h-96">
                  {JSON.stringify(result.output_data, null, 2)}
                </pre>
              </CardContent>
            )}
          </AccordionContent>
        </Card>
      </AccordionItem>
    </Accordion>
  );
}

export default function AnalysisPage() {
  const [patentId, setPatentId] = useState("");
  const [targetProduct, setTargetProduct] = useState("");
  const [pipeline, setPipeline] = useState<Pipeline>("C");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<JobResultsResponse | null>(null);

  const handleStartAnalysis = async () => {
    if (!patentId.trim()) {
      setError("特許番号を入力してください");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const request: StartAnalysisRequest = {
        patent_id: patentId,
        pipeline,
        target_product: targetProduct || undefined,
      };

      const response = await startAnalysis(request);

      // Get results
      const jobResults = await getJobResults(response.job_id);
      setResults(jobResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            特許侵害分析
          </CardTitle>
          <CardDescription>
            特許番号と対象製品を入力して、侵害分析を実行します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="analysisPatentId">特許番号 *</Label>
              <Input
                id="analysisPatentId"
                name="analysisPatentId"
                placeholder="例: JP1234567B2, 特許第1234567号"
                value={patentId}
                onChange={(e) => setPatentId(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="analysisTargetProduct">対象製品 (任意)</Label>
              <Input
                id="analysisTargetProduct"
                name="analysisTargetProduct"
                placeholder="例: iPhone 15 Pro"
                value={targetProduct}
                onChange={(e) => setTargetProduct(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>パイプライン</Label>
            <Tabs value={pipeline} onValueChange={(v) => setPipeline(v as Pipeline)}>
              <TabsList className="grid w-full grid-cols-4">
                {(Object.entries(PIPELINE_INFO) as [Pipeline, { name: string; description: string }][]).map(
                  ([key, info]) => (
                    <TabsTrigger key={key} value={key}>
                      {info.name}
                    </TabsTrigger>
                  )
                )}
              </TabsList>
              {(Object.entries(PIPELINE_INFO) as [Pipeline, { name: string; description: string }][]).map(
                ([key, info]) => (
                  <TabsContent key={key} value={key}>
                    <p className="text-sm text-muted-foreground mt-2">
                      {info.description}
                    </p>
                  </TabsContent>
                )
              )}
            </Tabs>
          </div>

          <Button
            onClick={handleStartAnalysis}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                分析中...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                分析を開始
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {results && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <StatusIcon status={results.status} />
                分析結果
              </CardTitle>
              <span className="text-sm text-muted-foreground">
                Job ID: {results.job_id.slice(0, 8)}...
              </span>
            </div>
            <CardDescription>
              ステータス: {results.status} | {results.results.length} ステージ完了
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.results.map((result, index) => (
              <StageResultCard key={index} result={result} />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
