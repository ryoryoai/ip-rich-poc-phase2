"use client";

import { useState } from "react";
import { Search, FileText, AlertCircle } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { resolvePatentNumber, getClaim, type ClaimResponse } from "@/lib/api";

export default function Home() {
  const [patentInput, setPatentInput] = useState("");
  const [claimNo, setClaimNo] = useState(1);
  const [result, setResult] = useState<ClaimResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resolvedPatent, setResolvedPatent] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!patentInput.trim()) {
      setError("特許番号を入力してください");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // First resolve the patent number
      const resolved = await resolvePatentNumber(patentInput);
      setResolvedPatent(resolved.normalized);

      // Then get the claim
      const claim = await getClaim(resolved.normalized, claimNo);
      setResult(claim);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Tabs defaultValue="search" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="search">請求項検索</TabsTrigger>
          <TabsTrigger value="about">使い方</TabsTrigger>
        </TabsList>

        <TabsContent value="search" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                特許番号から請求項を検索
              </CardTitle>
              <CardDescription>
                日本特許の番号を入力して、請求項の全文を取得します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Label htmlFor="patentNumber" className="mb-2 block">
                    特許番号
                  </Label>
                  <Input
                    id="patentNumber"
                    name="patentNumber"
                    placeholder="例: 特許第1234567号, JP1234567B2, 1234567"
                    value={patentInput}
                    onChange={(e) => setPatentInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  />
                </div>
                <div className="w-24">
                  <Label htmlFor="claimNo" className="mb-2 block">
                    請求項No.
                  </Label>
                  <Input
                    id="claimNo"
                    name="claimNo"
                    type="number"
                    min={1}
                    value={claimNo}
                    onChange={(e) => setClaimNo(parseInt(e.target.value) || 1)}
                  />
                </div>
              </div>
              <Button onClick={handleSearch} disabled={loading} className="w-full">
                {loading ? "検索中..." : "検索"}
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

          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {resolvedPatent} - 請求項{result.claim_no}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-muted p-4 rounded-md whitespace-pre-wrap font-mono text-sm">
                  {result.claim_text}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="about">
          <Card>
            <CardHeader>
              <CardTitle>使い方</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">対応する入力形式</h3>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  <li>特許第1234567号（日本語形式）</li>
                  <li>JP1234567B2（国際形式）</li>
                  <li>1234567（数字のみ）</li>
                  <li>特願2020-123456（出願番号）</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold mb-2">システム概要</h3>
                <p className="text-muted-foreground">
                  このシステムは、日本特許の請求項データを保存・検索するためのツールです。
                  事前に取り込んだ特許データから、指定した請求項の全文を取得できます。
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
