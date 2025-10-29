"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function AnalyzePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingPatent, setIsFetchingPatent] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [patentNumber, setPatentNumber] = useState("");
  const [patentInfo, setPatentInfo] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>("");

  // Step 1: Deep Researchで特許情報を取得
  const fetchPatentWithDeepResearch = async () => {
    if (!patentNumber.trim()) {
      setError("特許番号を入力してください");
      return;
    }

    setIsFetchingPatent(true);
    setError(null);
    setPatentInfo(null);
    setAnalysisResult(null);
    setCurrentStep("Deep Researchで特許情報を取得中...");

    try {
      // Deep Research APIを使用して特許情報と関連製品を一度に取得
      const response = await fetch("/api/analyze-deep", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patentNumber: patentNumber.trim(),
          mode: 'full' // 特許情報と潜在的侵害製品を両方取得
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Deep Research実行に失敗しました");
      }

      const data = await response.json();
      setPatentInfo(data);
      setCurrentStep("");

    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
      setCurrentStep("");
    } finally {
      setIsFetchingPatent(false);
    }
  };

  // Step 2: 侵害調査を実行
  const runInfringementAnalysis = async () => {
    if (!patentInfo) return;

    setIsAnalyzing(true);
    setError(null);
    setCurrentStep("侵害調査を実行中...");

    try {
      // 侵害調査の詳細分析を実行
      const response = await fetch("/api/analyze-simple", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patentId: patentNumber.trim()
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "侵害調査に失敗しました");
      }

      const data = await response.json();
      setAnalysisResult(data);
      setCurrentStep("");

    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
      setCurrentStep("");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadResult = () => {
    if (!analysisResult) return;
    const dataStr = JSON.stringify({
      patentInfo,
      analysisResult
    }, null, 2);
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `analysis_${patentNumber}_${Date.now()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-8">特許侵害調査分析（詳細版）</h1>

      {/* Step 1: 特許番号入力 */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Step 1: 特許番号入力</CardTitle>
          <CardDescription>
            Deep Researchで特許情報と関連製品を自動取得します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="patentNumber">特許番号</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  id="patentNumber"
                  placeholder="例: 07666636, US7666636, 特許第6195960号"
                  value={patentNumber}
                  onChange={(e) => {
                    console.log('Input changed:', e.target.value);
                    setPatentNumber(e.target.value);
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && patentNumber.length > 0) {
                      fetchPatentWithDeepResearch();
                    }
                  }}
                  disabled={isFetchingPatent || isAnalyzing}
                />
                <Button
                  type="button"
                  onClick={() => {
                    console.log('Button clicked, patentNumber:', patentNumber);
                    fetchPatentWithDeepResearch();
                  }}
                  disabled={patentNumber.length === 0 || isFetchingPatent || isAnalyzing}
                  className="min-w-[180px]"
                >
                  {isFetchingPatent ? "Deep Research実行中..." : "特許情報取得"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                O4 Mini Deep Researchモデルが特許情報と潜在的侵害製品を自動検出します
              </p>
              {/* デバッグ情報 */}
              {process.env.NODE_ENV === 'development' && (
                <div className="text-xs text-gray-400 mt-2 p-2 bg-gray-100 rounded">
                  <p>Debug Info:</p>
                  <p>patentNumber: "{patentNumber}"</p>
                  <p>patentNumber.length: {patentNumber.length}</p>
                  <p>patentNumber.trim(): "{patentNumber.trim()}"</p>
                  <p>!patentNumber.trim(): {String(!patentNumber.trim())}</p>
                  <p>isFetchingPatent: {String(isFetchingPatent)}</p>
                  <p>isAnalyzing: {String(isAnalyzing)}</p>
                  <p>Button disabled: {String(patentNumber.length === 0 || isFetchingPatent || isAnalyzing)}</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* エラー表示 */}
      {error && (
        <Card className="mb-8 border-red-500">
          <CardHeader>
            <CardTitle className="text-red-600">エラー</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* 処理中表示 */}
      {(isFetchingPatent || isAnalyzing) && currentStep && (
        <Card className="mb-8">
          <CardContent className="py-8">
            <div className="text-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="font-medium">{currentStep}</p>
              <p className="text-xs text-gray-500">
                ※ Deep Researchは通常1〜3分程度かかります（包括的な調査のため）
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span className="text-xs">リクエストを送信しました</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span className="text-xs">Deep Researchが処理中...</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-gray-300 rounded-full"></div>
                  <span className="text-xs text-gray-400">結果を取得中...</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: 取得した特許情報の表示 */}
      {patentInfo && !analysisResult && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Step 2: 取得した特許情報</CardTitle>
            <CardDescription>
              Deep Researchで取得した情報を確認してください
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 特許基本情報 */}
            <div className="space-y-2">
              <h3 className="font-semibold text-lg">特許情報</h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <p><span className="font-medium">特許番号:</span> {patentInfo.patentNumber}</p>
                {patentInfo.patentTitle && (
                  <p><span className="font-medium">発明の名称:</span> {patentInfo.patentTitle}</p>
                )}
                {patentInfo.assignee && (
                  <p><span className="font-medium">特許権者:</span> {patentInfo.assignee}</p>
                )}
              </div>
            </div>

            {/* 請求項1 */}
            {patentInfo.claim1 && (
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">請求項1</h3>
                <div className="bg-blue-50 p-4 rounded-lg max-h-60 overflow-y-auto">
                  <p className="whitespace-pre-wrap text-sm">{patentInfo.claim1}</p>
                </div>
              </div>
            )}

            {/* Deep Researchで検出された潜在的侵害製品 */}
            {patentInfo.potentialInfringers && patentInfo.potentialInfringers.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">検出された潜在的侵害製品</h3>
                <div className="space-y-2">
                  {patentInfo.potentialInfringers.map((product: any, index: number) => (
                    <div key={index} className="border p-3 rounded-lg bg-yellow-50">
                      <p className="font-medium">{product.company} - {product.product}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        侵害可能性: {product.probability || '調査中'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deep Research結果の生データ */}
            {patentInfo.deepSearchResult && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800">
                  Deep Research結果の詳細を表示
                </summary>
                <div className="mt-2 p-3 bg-gray-50 rounded-lg">
                  <pre className="whitespace-pre-wrap text-xs overflow-x-auto">
                    {patentInfo.deepSearchResult}
                  </pre>
                </div>
              </details>
            )}

            {/* 侵害調査開始ボタン */}
            <div className="pt-4 border-t">
              <Button
                onClick={runInfringementAnalysis}
                disabled={isAnalyzing}
                className="w-full"
                size="lg"
              >
                {isAnalyzing ? "侵害調査実行中..." : "侵害調査を開始"}
              </Button>
              <p className="text-xs text-muted-foreground text-center mt-2">
                検出された製品について詳細な侵害調査を実行します
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: 侵害調査結果 */}
      {analysisResult && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Step 3: 侵害調査結果</CardTitle>
            <CardDescription>
              {new Date(analysisResult.analysisDate).toLocaleString('ja-JP')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* サマリー */}
            {analysisResult.summary && (
              <div className={`p-4 rounded-lg ${
                analysisResult.summary.includes('侵害可能性') ? 'bg-red-50' : 'bg-green-50'
              }`}>
                <h3 className="font-semibold mb-2">調査サマリー</h3>
                <p>{analysisResult.summary}</p>
              </div>
            )}

            {/* 詳細な侵害分析結果 */}
            <div className="space-y-2">
              <h3 className="font-semibold text-lg">構成要件充足性分析</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="whitespace-pre-wrap text-xs overflow-x-auto">
                  {analysisResult.infringementAnalysis}
                </pre>
              </div>
            </div>

            {/* 検出された製品の詳細 */}
            {analysisResult.detectedProducts && analysisResult.detectedProducts.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">製品別充足性判定</h3>
                <div className="space-y-2">
                  {analysisResult.detectedProducts.map((product: any, index: number) => (
                    <div key={index} className="border p-3 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{product.product}</p>
                          {product.company && (
                            <p className="text-sm text-gray-600">{product.company}</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs rounded ${
                          product.compliance === '○'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {product.compliance === '○' ? '充足' : '非充足'}
                        </span>
                      </div>
                      {product.evidence && (
                        <p className="text-sm text-gray-600 mt-2">根拠: {product.evidence}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ダウンロードボタン */}
            <div className="pt-4 border-t flex justify-end">
              <Button onClick={downloadResult} variant="outline">
                結果をJSONでダウンロード
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </main>
  );
}