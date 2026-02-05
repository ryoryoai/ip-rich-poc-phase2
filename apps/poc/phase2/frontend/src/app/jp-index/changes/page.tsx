"use client";

import { useState } from "react";
import Link from "next/link";
import { CalendarClock, AlertCircle, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getJpIndexChanges, type JpIndexChangesResponse } from "@/lib/api";

function todayISO(): string {
  const now = new Date();
  return now.toISOString().slice(0, 10);
}

export default function JpIndexChangesPage() {
  const [fromDate, setFromDate] = useState(todayISO());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JpIndexChangesResponse | null>(null);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getJpIndexChanges(fromDate);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarClock className="h-5 w-5" />
            更新差分一覧
          </CardTitle>
          <CardDescription>
            指定日以降に更新があった案件を一覧表示します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-end gap-4">
            <div className="flex-1 space-y-2">
              <Label htmlFor="jpIndexChangesFrom">更新日 From</Label>
              <Input
                id="jpIndexChangesFrom"
                name="jpIndexChangesFrom"
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <Button onClick={handleFetch} disabled={loading}>
              {loading ? "取得中..." : "取得"}
            </Button>
          </div>
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
            <CardTitle>差分結果</CardTitle>
            <CardDescription>
              {result.from_date} 以降の更新: {result.count} 件
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.items.length === 0 && (
              <div className="text-sm text-muted-foreground">
                更新案件はありません。
              </div>
            )}
            {result.items.map((item) => (
              <div
                key={item.case_id}
                className="border rounded-md p-4 flex items-start justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">
                    {item.application_number || "番号未設定"}
                  </div>
                  <div className="font-semibold">
                    {item.title || "タイトル未取得"}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    状態: {item.status || "未設定"} / 更新日:{" "}
                    {item.last_update_date || "不明"}
                  </div>
                </div>
                <Link
                  href={`/jp-index/${item.case_id}`}
                  className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                >
                  詳細
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
