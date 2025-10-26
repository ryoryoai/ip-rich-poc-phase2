"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AnalyzeRequest, AnalyzeResponse } from "@/types/api";

export default function AnalyzePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<AnalyzeRequest>({
    patentNumber: "",
    claimText: "",
    companyName: "",
    productName: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "分析に失敗しました");
      }

      const data: AnalyzeResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "予期しないエラーが発生しました");
    } finally {
      setIsLoading(false);
    }
  };

  const downloadResult = () => {
    if (!result) return;
    const dataStr = JSON.stringify(result, null, 2);
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `analysis_${result.patentNumber}_${Date.now()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">特許侵害調査分析</h1>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>分析入力</CardTitle>
          <CardDescription>
            特許情報と調査対象の製品情報を入力してください
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="patentNumber">特許番号</Label>
              <Input
                id="patentNumber"
                placeholder="例: 06195960"
                value={formData.patentNumber}
                onChange={(e) =>
                  setFormData({ ...formData, patentNumber: e.target.value })
                }
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <Label htmlFor="claimText">請求項1</Label>
              <Textarea
                id="claimText"
                placeholder="請求項1の全文を入力してください"
                rows={8}
                value={formData.claimText}
                onChange={(e) =>
                  setFormData({ ...formData, claimText: e.target.value })
                }
                required
                disabled={isLoading}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="companyName">企業名</Label>
                <Input
                  id="companyName"
                  placeholder="例: TeamViewer"
                  value={formData.companyName}
                  onChange={(e) =>
                    setFormData({ ...formData, companyName: e.target.value })
                  }
                  required
                  disabled={isLoading}
                />
              </div>

              <div>
                <Label htmlFor="productName">製品名</Label>
                <Input
                  id="productName"
                  placeholder="例: TeamViewer Assist AR"
                  value={formData.productName}
                  onChange={(e) =>
                    setFormData({ ...formData, productName: e.target.value })
                  }
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? "分析中..." : "分析開始"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card className="mb-8 border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">エラー</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <>
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>分析結果サマリー</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">特許番号</p>
                  <p className="font-semibold">{result.patentNumber}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">製品</p>
                  <p className="font-semibold">
                    {result.companyName} - {result.productName}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">構成要件数</p>
                  <p className="font-semibold">{result.summary.totalRequirements}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">充足要件数</p>
                  <p className="font-semibold">
                    {result.summary.compliantRequirements} / {result.summary.totalRequirements}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">充足率</p>
                  <p className="font-semibold">{result.summary.complianceRate.toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">侵害可能性</p>
                  <p className={`font-bold text-lg ${
                    result.summary.infringementPossibility === "○"
                      ? "text-destructive"
                      : "text-green-600"
                  }`}>
                    {result.summary.infringementPossibility === "○" ? "高い" : "低い"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle>構成要件一覧</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {result.requirements.map((req, index) => (
                  <div key={index} className="p-3 border rounded">
                    <p className="font-medium">{req.id}</p>
                    <p className="text-sm">{req.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle>充足性判定結果</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {result.complianceResults.map((item, index) => (
                  <div key={index} className="p-4 border rounded">
                    <div className="flex justify-between mb-2">
                      <p className="font-medium">{item.requirementId}</p>
                      <span className={`px-2 py-1 rounded text-sm font-bold ${
                        item.compliance === "○"
                          ? "bg-destructive/10 text-destructive"
                          : "bg-green-100 text-green-700"
                      }`}>
                        {item.compliance === "○" ? "充足" : "非充足"}
                      </span>
                    </div>
                    <p className="text-sm mb-2">{item.requirement}</p>
                    <p className="text-sm text-muted-foreground mb-1">
                      <strong>理由:</strong> {item.reason}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      <strong>根拠:</strong> {item.evidence}
                    </p>
                  </div>
                ))}
              </div>
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