'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export default function ResearchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patentNumber, setPatentNumber] = useState('');
  const [claimText, setClaimText] = useState('');

  const handleSubmit = async () => {
    if (!patentNumber.trim()) {
      setError('特許番号を入力してください');
      return;
    }

    if (!claimText.trim()) {
      setError('請求項1を入力してください');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // ジョブを作成（Deep Researchは非同期で実行される）
      const res = await fetch('/api/analyze/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patentNumber: patentNumber.trim(),
          claimText: claimText.trim(),
          companyName: '調査中...', // Deep Researchで取得される
          productName: '調査中...', // Deep Researchで取得される
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Failed to start analysis');
      }

      // 既存のジョブが見つかった場合は結果ページへ遷移
      if (data.existing) {
        router.push(`/research/result/${data.job_id}`);
      } else {
        // 新規ジョブの場合はステータスページへ遷移（Deep Research実行中）
        router.push(`/research/status/${data.job_id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setLoading(false);
    }
  };

  return (
    <main className="container mx-auto p-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-8">特許侵害調査分析（DB保存版）</h1>

      <div className="mb-6">
        <a
          href="/research/list"
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          ← 分析履歴一覧を見る
        </a>
      </div>

      {/* Step 1: 特許番号入力 */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Step 1: 特許番号入力</CardTitle>
          <CardDescription>
            Deep Researchで特許情報と関連製品を自動取得し、データベースに保存します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="patentNumber">特許番号</Label>
              <Input
                id="patentNumber"
                placeholder="例: 07666636, US7666636, 特許第6195960号"
                value={patentNumber}
                onChange={(e) => setPatentNumber(e.target.value)}
                disabled={loading}
                className="mt-2"
              />
            </div>

            <div>
              <Label htmlFor="claimText">請求項1（全文）</Label>
              <Textarea
                id="claimText"
                placeholder="請求項1の全文を入力してください"
                value={claimText}
                onChange={(e) => setClaimText(e.target.value)}
                disabled={loading}
                className="mt-2 min-h-[200px] font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground mt-1">
                ※ 請求項1の全文をそのまま貼り付けてください（正確な侵害判定に必要です）
              </p>
            </div>

            <div className="flex justify-end">
              <Button
                type="button"
                onClick={handleSubmit}
                disabled={patentNumber.length === 0 || claimText.length === 0 || loading}
                className="min-w-[200px]"
              >
                {loading ? 'Deep Research実行中...' : '侵害調査を開始'}
              </Button>
            </div>

            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">
                O4 Mini Deep Researchモデルが潜在的侵害製品を自動検出し、データベースに保存します
              </p>
              <p className="text-xs text-yellow-600">
                ※ 同じ特許番号で過去に分析済みの場合は、既存の結果を表示します
              </p>
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
      {loading && (
        <Card className="mb-8">
          <CardContent className="py-8">
            <div className="text-center space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="font-medium">Deep Researchで特許情報を取得中...</p>
              <p className="text-xs text-gray-500">
                ※ Deep Researchは通常1〜3分程度かかります（包括的な調査のため）
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center space-x-2 justify-center">
                  <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span className="text-xs">リクエストを送信しました</span>
                </div>
                <div className="flex items-center space-x-2 justify-center">
                  <div className="h-2 w-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span className="text-xs">Deep Researchが処理中...</span>
                </div>
                <div className="flex items-center space-x-2 justify-center">
                  <div className="h-2 w-2 bg-gray-300 rounded-full"></div>
                  <span className="text-xs text-gray-400">データベースに保存中...</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
