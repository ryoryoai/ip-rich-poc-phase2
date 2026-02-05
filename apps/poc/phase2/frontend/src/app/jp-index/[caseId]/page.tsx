"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FileText, AlertCircle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getJpIndexCase, type JpIndexCaseDetail } from "@/lib/api";

export default function JpIndexCaseDetailPage() {
  const params = useParams();
  const caseId = params.caseId as string;
  const [data, setData] = useState<JpIndexCaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchCase = async () => {
      setLoading(true);
      setError(null);
      try {
        const detail = await getJpIndexCase(caseId);
        setData(detail);
      } catch (err) {
        setError(err instanceof Error ? err.message : "取得に失敗しました");
      } finally {
        setLoading(false);
      }
    };
    if (caseId) {
      fetchCase();
    }
  }, [caseId]);

  if (loading) {
    return <div className="text-sm text-muted-foreground">読み込み中...</div>;
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const { case: caseInfo } = data;

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {caseInfo.title || "タイトル未取得"}
          </CardTitle>
          <CardDescription>
            出願番号: {caseInfo.application_number_norm || "未設定"} / 状態:{" "}
            {caseInfo.current_status || "未設定"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div>出願番号 (原文): {caseInfo.application_number_raw || "-"}</div>
          <div>出願日: {caseInfo.filing_date || "-"}</div>
          <div>登録日: {caseInfo.registration_date || "-"}</div>
          <div>
            特許番号:{" "}
            {caseInfo.patent_numbers && caseInfo.patent_numbers.length > 0
              ? caseInfo.patent_numbers.join(", ")
              : "-"}
          </div>
          <div>更新日: {caseInfo.last_update_date || "-"}</div>
          <div>状態更新日: {caseInfo.status_updated_at || "-"}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>番号相互参照</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.numbers.length === 0 && <div>登録なし</div>}
          {data.numbers.map((n, index) => (
            <div key={`${n.number_norm}-${index}`}>
              {n.type}: {n.number_norm} {n.kind ? `(${n.kind})` : ""}{" "}
              {n.is_primary ? "[primary]" : ""}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>文献</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {data.documents.length === 0 && <div>登録なし</div>}
          {data.documents.map((doc, index) => (
            <div key={`${doc.doc_type}-${index}`} className="border rounded p-3">
              <div>種別: {doc.doc_type}</div>
              <div>公開番号: {doc.publication_number_norm || "-"}</div>
              <div>特許番号: {doc.patent_number_norm || "-"}</div>
              <div>公開日: {doc.publication_date || "-"}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>出願人</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.applicants.length === 0 && <div>登録なし</div>}
          {data.applicants.map((app, index) => (
            <div key={`${app.name_raw}-${index}`}>
              {app.name_raw} {app.is_primary ? "[primary]" : ""} / role:{" "}
              {app.role}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>分類</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.classifications.length === 0 && <div>登録なし</div>}
          {data.classifications.map((c, index) => (
            <div key={`${c.type}-${c.code}-${index}`}>
              {c.type}: {c.code} {c.is_primary ? "[primary]" : ""}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>状態イベント</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.status_events.length === 0 && <div>登録なし</div>}
          {data.status_events.map((ev, index) => (
            <div key={`${ev.event_type}-${index}`}>
              {ev.event_date || "-"} / {ev.event_type} {ev.source ? `(${ev.source})` : ""}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>状態スナップショット</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {data.status_snapshots.length === 0 && <div>登録なし</div>}
          {data.status_snapshots.map((snapshot, index) => (
            <div key={`${snapshot.status}-${index}`} className="border rounded p-3">
              <div>ステータス: {snapshot.status}</div>
              <div>算出日時: {snapshot.derived_at || "-"}</div>
              <div>ロジック: {snapshot.logic_version}</div>
              <div>理由: {snapshot.reason || "-"}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
