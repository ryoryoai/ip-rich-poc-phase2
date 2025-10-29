"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SimplePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [patentId, setPatentId] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [patentInfo, setPatentInfo] = useState<any>(null);
  const [claim1, setClaim1] = useState<string>("");

  const handleAnalyze = async () => {
    if (!patentId.trim()) {
      setError("特許IDを入力してください");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setPatentInfo(null);
    setClaim1("");
    setCurrentStep("Step 1: J-PlatPatから特許情報を取得中...");

    try {
      // タイムアウトを設定して段階的に表示を更新
      setTimeout(() => {
        if (isLoading) {
          setCurrentStep("Step 1: 特許番号を検索中...");
        }
      }, 2000);

      setTimeout(() => {
        if (isLoading) {
          setCurrentStep("Step 1: 請求項1を抽出中...");
        }
      }, 5000);

      const response = await fetch("/api/analyze-simple", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ patentId: patentId.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "分析に失敗しました");
      }

      const data = await response.json();

      // 取得した請求項1を表示
      if (data.claim1) {
        setClaim1(data.claim1);
        setCurrentStep("Step 2: Deep Searchで侵害製品を調査中...");

        // 少し遅延を入れて視覚的にステップを示す
        await new Promise(resolve => setTimeout(resolve, 1000));

        setTimeout(() => {
          if (isLoading) {
            setCurrentStep("Step 2: 構成要件を分析中...");
          }
        }, 2000);

        setTimeout(() => {
          if (isLoading) {
            setCurrentStep("Step 2: 製品との充足性を判定中...");
          }
        }, 5000);
      }

      setResult(data);
      setCurrentStep("分析完了");
    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
      setCurrentStep("");
    } finally {
      setTimeout(() => {
        setIsLoading(false);
        setCurrentStep("");
      }, 1000);
    }
  };

  const downloadResult = () => {
    if (!result) return;
    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `infringement_analysis_${result.patentId}_${Date.now()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  return (
    <main className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-2">特許侵害調査システム</h1>
      <p className="text-gray-600 mb-8">特許IDを入力するだけで、J-PlatPatから情報を取得し、侵害可能性のある製品を自動検出します</p>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>特許ID入力</CardTitle>
          <CardDescription>
            分析したい特許のIDを入力してください
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="patentId">特許ID</Label>
            <div className="flex gap-2 mt-2">
              <Input
                id="patentId"
                placeholder="例: 特許第6195960号, 2020-123456, US7666636"
                value={patentId}
                onChange={(e) => setPatentId(e.target.value)}
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAnalyze();
                  }
                }}
              />
              <Button
                onClick={handleAnalyze}
                disabled={isLoading || !patentId.trim()}
                className="min-w-[120px]"
              >
                {isLoading ? "分析中..." : "侵害調査開始"}
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              ※ J-PlatPatから請求項1を自動取得し、侵害可能性のある製品を検出します
            </p>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="mb-8 border-red-500">
          <CardHeader>
            <CardTitle className="text-red-600">エラー</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-red-600 font-medium">{error}</p>
            <details className="mt-2">
              <summary className="text-sm text-gray-600 cursor-pointer hover:text-gray-800">
                詳細情報を表示
              </summary>
              <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify({
                  timestamp: new Date().toISOString(),
                  patentId: patentId,
                  error: error,
                  hint: "O4 Mini Deep ResearchモデルはまだAPI応答形式が安定していない可能性があります。通常のGPT-4モデルにフォールバックしています。"
                }, null, 2)}
              </pre>
            </details>
          </CardContent>
        </Card>
      )}

      {isLoading && (
        <Card className="mb-8">
          <CardContent className="py-8">
            <div className="space-y-6">
              {/* プログレス表示 */}
              <div className="text-center space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <div className="space-y-2">
                  <p className="font-medium text-lg">{currentStep || "処理中..."}</p>
                  <p className="text-xs text-gray-500">※ 処理には30秒〜1分程度かかる場合があります</p>
                </div>
              </div>

              {/* 取得済みの請求項1を先行表示 */}
              {claim1 && (
                <div className="space-y-2 border-t pt-4">
                  <h3 className="font-semibold text-sm text-green-600">✓ Step 1完了: 請求項1を取得しました</h3>
                  <div className="bg-blue-50 p-3 rounded-lg max-h-40 overflow-y-auto">
                    <p className="whitespace-pre-wrap text-xs">{claim1}</p>
                  </div>
                </div>
              )}

              {/* ステップインジケーター */}
              <div className="border-t pt-4">
                <div className="flex justify-between text-xs">
                  <div className={`flex-1 text-center ${currentStep.includes('Step 1') ? 'text-blue-600 font-bold' : claim1 ? 'text-green-600' : 'text-gray-400'}`}>
                    <div className={`w-8 h-8 mx-auto mb-1 rounded-full flex items-center justify-center ${
                      claim1 ? 'bg-green-100 text-green-600' :
                      currentStep.includes('Step 1') ? 'bg-blue-100 text-blue-600' :
                      'bg-gray-100 text-gray-400'
                    }`}>
                      {claim1 ? '✓' : '1'}
                    </div>
                    <p>特許情報取得</p>
                  </div>
                  <div className={`flex-1 text-center ${currentStep.includes('Step 2') ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>
                    <div className={`w-8 h-8 mx-auto mb-1 rounded-full flex items-center justify-center ${
                      currentStep.includes('Step 2') ? 'bg-blue-100 text-blue-600' :
                      'bg-gray-100 text-gray-400'
                    }`}>
                      2
                    </div>
                    <p>侵害調査</p>
                  </div>
                  <div className="flex-1 text-center text-gray-400">
                    <div className="w-8 h-8 mx-auto mb-1 rounded-full bg-gray-100 text-gray-400 flex items-center justify-center">
                      3
                    </div>
                    <p>結果表示</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {result && (
        <>
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>分析結果</CardTitle>
              <CardDescription>
                {new Date(result.analysisDate).toLocaleString('ja-JP')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 特許情報 */}
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">特許情報</h3>
                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                  <p><span className="font-medium">特許番号:</span> {result.patentId}</p>
                  {result.patentTitle && (
                    <p><span className="font-medium">発明の名称:</span> {result.patentTitle}</p>
                  )}
                  {result.patentHolder && (
                    <p><span className="font-medium">特許権者:</span> {result.patentHolder}</p>
                  )}
                  {result.inventionSummary && (
                    <div className="mt-2 pt-2 border-t">
                      <p className="font-medium mb-1">発明の内容:</p>
                      <p className="text-sm text-gray-700">{result.inventionSummary}</p>
                    </div>
                  )}
                  {result.technicalField && (
                    <p className="text-sm"><span className="font-medium">技術分野:</span> {result.technicalField}</p>
                  )}
                </div>
              </div>

              {/* 請求項1 */}
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">請求項1</h3>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="whitespace-pre-wrap text-sm">{result.claim1}</p>
                </div>
              </div>

              {/* サマリー */}
              {result.summary && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg">調査サマリー</h3>
                  <div className={`p-4 rounded-lg ${
                    result.summary.includes('侵害可能性') ? 'bg-red-50' : 'bg-green-50'
                  }`}>
                    <p>{result.summary}</p>
                  </div>
                </div>
              )}

              {/* 侵害分析結果 */}
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">侵害調査結果</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="whitespace-pre-wrap text-xs overflow-x-auto">
                    {result.infringementAnalysis}
                  </pre>
                </div>
              </div>

              {/* 検出された製品 */}
              {result.detectedProducts && result.detectedProducts.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg">検出された製品</h3>
                  <div className="space-y-2">
                    {result.detectedProducts.map((product: any, index: number) => (
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
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={downloadResult} variant="outline">
              結果をJSONでダウンロード
            </Button>
          </div>
        </>
      )}
    </main>
  );
}