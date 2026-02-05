"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, AlertCircle, ChevronRight } from "lucide-react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { searchJpIndex, type JpIndexSearchResponse } from "@/lib/api";

const STATUS_OPTIONS = [
  { value: "all", label: "すべて" },
  { value: "pending", label: "審査中/係属" },
  { value: "granted", label: "登録" },
  { value: "expired", label: "失効" },
  { value: "withdrawn", label: "取下" },
  { value: "abandoned", label: "放棄" },
  { value: "rejected", label: "拒絶" },
];

export default function JpIndexSearchPage() {
  const [q, setQ] = useState("");
  const [number, setNumber] = useState("");
  const [applicant, setApplicant] = useState("");
  const [classification, setClassification] = useState("");
  const [status, setStatus] = useState("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JpIndexSearchResponse | null>(null);

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await searchJpIndex({
        q: q || undefined,
        number: number || undefined,
        applicant: applicant || undefined,
        classification: classification || undefined,
        status: status === "all" ? undefined : status,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        page: 1,
        page_size: 20,
        sort: "updated_desc",
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "検索に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            JP Patent Index 検索
          </CardTitle>
          <CardDescription>
            番号・キーワード・出願人・分類・状態で特許リストを検索します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="jpIndexKeyword">キーワード</Label>
              <Input
                id="jpIndexKeyword"
                name="jpIndexKeyword"
                placeholder="タイトル/要約"
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="jpIndexNumber">番号検索</Label>
              <Input
                id="jpIndexNumber"
                name="jpIndexNumber"
                placeholder="出願/公開/特許番号"
                value={number}
                onChange={(e) => setNumber(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="jpIndexApplicant">出願人</Label>
              <Input
                id="jpIndexApplicant"
                name="jpIndexApplicant"
                placeholder="社名（表記ゆれ含む）"
                value={applicant}
                onChange={(e) => setApplicant(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="jpIndexClassification">分類（IPC/FI/Fターム）</Label>
              <Input
                id="jpIndexClassification"
                name="jpIndexClassification"
                placeholder="例: G06F, 5B057"
                value={classification}
                onChange={(e) => setClassification(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="jpIndexStatus">状態</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger id="jpIndexStatus">
                  <SelectValue placeholder="状態を選択" />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="jpIndexFromDate">更新日 From</Label>
                <Input
                  id="jpIndexFromDate"
                  name="jpIndexFromDate"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="jpIndexToDate">更新日 To</Label>
                <Input
                  id="jpIndexToDate"
                  name="jpIndexToDate"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </div>
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
            <CardTitle>検索結果</CardTitle>
            <CardDescription>
              {result.total} 件（表示 {result.items.length} 件）
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.items.length === 0 && (
              <div className="text-sm text-muted-foreground">
                該当する結果がありません。
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
