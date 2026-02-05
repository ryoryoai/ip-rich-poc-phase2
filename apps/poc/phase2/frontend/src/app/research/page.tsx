"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { startAnalysis } from "@/lib/api";

export default function ResearchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patentNumber, setPatentNumber] = useState("");
  const [claimText, setClaimText] = useState("");
  const [targetProduct, setTargetProduct] = useState("");
  const [patentNumberError, setPatentNumberError] = useState<string | null>(null);
  const [claimTextError, setClaimTextError] = useState<string | null>(null);
  const patentNumberRef = useRef<HTMLInputElement>(null);
  const claimTextRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async () => {
    if (loading) return;
    setPatentNumberError(null);
    setClaimTextError(null);

    if (!patentNumber.trim()) {
      setPatentNumberError("特許番号を入力してください。");
      patentNumberRef.current?.focus();
      return;
    }

    if (!claimText.trim()) {
      setClaimTextError("請求項を入力してください。");
      claimTextRef.current?.focus();
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await startAnalysis({
        patent_id: patentNumber.trim(),
        target_product: targetProduct.trim() || undefined,
        pipeline: "C", // Default to main analysis pipeline
      });

      router.push(`/research/status/${result.job_id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "分析の開始に失敗しました。時間をおいて再試行してください。"
      );
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-8">特許侵害調査分析</h1>

      <div className="mb-6">
        <Link
          href="/research/list"
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          ← 分析履歴一覧を見る
        </Link>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>新規分析を開始</CardTitle>
          <CardDescription>
            特許番号と請求項を入力して、侵害分析を実行します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="patentNumber" className="mb-2 block">
                特許番号
              </Label>
              <Input
                id="patentNumber"
                name="patentNumber"
                ref={patentNumberRef}
                placeholder="例: JP1234567B2, 特許第1234567号"
                value={patentNumber}
                onChange={(e) => {
                  setPatentNumber(e.target.value);
                  setPatentNumberError(null);
                }}
                disabled={loading}
              />
              {patentNumberError && (
                <p className="mt-1 text-xs text-red-600">{patentNumberError}</p>
              )}
            </div>

            <div>
              <Label htmlFor="claimText" className="mb-2 block">
                請求項（全文）
              </Label>
              <Textarea
                id="claimText"
                name="claimText"
                ref={claimTextRef}
                placeholder="例: 〜を備えた装置であって…"
                value={claimText}
                onChange={(e) => {
                  setClaimText(e.target.value);
                  setClaimTextError(null);
                }}
                disabled={loading}
                className="min-h-[200px] font-mono text-sm"
              />
              {claimTextError && (
                <p className="mt-1 text-xs text-red-600">{claimTextError}</p>
              )}
            </div>

            <div>
              <Label htmlFor="targetProduct" className="mb-2 block">
                対象製品（オプション）
              </Label>
              <Input
                id="targetProduct"
                name="targetProduct"
                placeholder="例: iPhone 15 Pro"
                value={targetProduct}
                onChange={(e) => setTargetProduct(e.target.value)}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground mt-1">
                特定の製品を調査対象にする場合は入力してください
              </p>
            </div>

            <div className="flex justify-end">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className="min-w-[200px]"
              >
                {loading ? "分析開始中…" : "侵害調査を開始"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="mb-8">
          <AlertTitle>エラー</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading && (
        <Card className="mb-8">
          <CardContent className="py-8">
            <div className="text-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="font-medium">分析を開始しています…</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
