"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  getCase,
  updateCase,
  type CaseDetailResponse,
  type CaseMatchItem,
} from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  draft: "下書き",
  exploring: "調査中",
  reviewing: "レビュー中",
  confirmed: "確定",
  archived: "アーカイブ",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "text-gray-600 bg-gray-100",
  exploring: "text-blue-600 bg-blue-100",
  reviewing: "text-yellow-600 bg-yellow-100",
  confirmed: "text-green-600 bg-green-100",
  archived: "text-muted-foreground bg-muted",
};

const STATUS_FLOW = ["draft", "exploring", "reviewing", "confirmed", "archived"];

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null || score === undefined) {
    return <span className="text-xs text-muted-foreground">-</span>;
  }
  const pct = Math.round(score * 100);
  let color = "text-gray-600 bg-gray-100";
  if (pct >= 70) color = "text-red-600 bg-red-100";
  else if (pct >= 40) color = "text-yellow-600 bg-yellow-100";
  else if (pct > 0) color = "text-green-600 bg-green-100";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>
      {pct}%
    </span>
  );
}

function MatchCard({ match }: { match: CaseMatchItem }) {
  return (
    <Card className="mb-2">
      <CardContent className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-sm">
              {match.product_name || "製品不明"}
              {match.company_name && (
                <span className="text-muted-foreground ml-2">({match.company_name})</span>
              )}
            </p>
            {match.reviewer_note && (
              <p className="text-xs text-muted-foreground mt-1">{match.reviewer_note}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <ScoreBadge score={match.score_total} />
            {match.status && (
              <span className="text-xs text-muted-foreground">{match.status}</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = params.case_id as string;

  const [data, setData] = useState<CaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    async function fetchCase() {
      try {
        const result = await getCase(caseId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "案件の取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    fetchCase();
  }, [caseId]);

  const handleStatusChange = async (newStatus: string) => {
    if (!data) return;
    setUpdating(true);
    try {
      const updated = await updateCase(caseId, { status: newStatus });
      setData({
        ...data,
        case: updated,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ステータス更新に失敗しました");
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-muted-foreground text-sm">読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>エラー</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!data) return null;

  const c = data.case;
  const currentIdx = STATUS_FLOW.indexOf(c.status);
  const nextStatus = currentIdx < STATUS_FLOW.length - 1 ? STATUS_FLOW[currentIdx + 1] : null;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <Link href="/cases" className="text-blue-600 hover:text-blue-800 text-sm">
          &larr; 案件一覧に戻る
        </Link>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{c.title}</h1>
          {c.description && (
            <p className="text-muted-foreground mt-1">{c.description}</p>
          )}
        </div>
        <span
          className={`text-sm px-3 py-1 rounded-full ${STATUS_COLORS[c.status] || "bg-gray-100"}`}
        >
          {STATUS_LABELS[c.status] || c.status}
        </span>
      </div>

      {/* Overview Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">案件情報</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">作成日</p>
              <p>{new Date(c.created_at).toLocaleDateString("ja-JP")}</p>
            </div>
            <div>
              <p className="text-muted-foreground">更新日</p>
              <p>{new Date(c.updated_at).toLocaleDateString("ja-JP")}</p>
            </div>
            <div>
              <p className="text-muted-foreground">調査対象</p>
              <p>{data.targets.length} 件</p>
            </div>
            <div>
              <p className="text-muted-foreground">候補</p>
              <p>{data.matches.length} 件</p>
            </div>
          </div>

          {nextStatus && (
            <div className="mt-4 pt-4 border-t">
              <Button
                size="sm"
                onClick={() => handleStatusChange(nextStatus)}
                disabled={updating}
              >
                {updating
                  ? "更新中..."
                  : `${STATUS_LABELS[nextStatus] || nextStatus} に進める`}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Targets */}
      {data.targets.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">調査対象</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.targets.map((t) => (
                <div key={t.id} className="flex items-center gap-3 text-sm">
                  <span className="text-xs px-2 py-0.5 rounded bg-muted">
                    {t.target_type}
                  </span>
                  <span className="font-mono text-xs">{t.target_id}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Matches */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-base">
            マッチ候補 ({data.matches.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data.matches.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              まだ候補がありません。分析を実行するとマッチ候補が生成されます。
            </p>
          ) : (
            <div>
              {data.matches.map((m) => (
                <MatchCard key={m.id} match={m} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
