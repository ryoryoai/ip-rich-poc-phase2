"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  fetchReviewQueue,
  reviewCompanyProductLink,
  reviewPatentCompanyLink,
  type ReviewQueueItem,
} from "@/lib/api";

export default function ReviewQueuePage() {
  const [reviewedBy, setReviewedBy] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patentLinks, setPatentLinks] = useState<ReviewQueueItem[]>([]);
  const [companyProductLinks, setCompanyProductLinks] = useState<ReviewQueueItem[]>([]);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const totalLinks = useMemo(
    () => patentLinks.length + companyProductLinks.length,
    [patentLinks.length, companyProductLinks.length]
  );

  const loadQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReviewQueue();
      setPatentLinks(data.patent_company_links);
      setCompanyProductLinks(data.company_product_links);
    } catch (err) {
      setError(err instanceof Error ? err.message : "レビューキュー取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleReview = async (
    type: "patent" | "company-product",
    linkId: string,
    decision: "approve" | "reject"
  ) => {
    setError(null);
    try {
      const note = notes[linkId]?.trim() || undefined;
      if (type === "patent") {
        await reviewPatentCompanyLink(
          linkId,
          decision,
          reviewedBy.trim() || undefined,
          note
        );
        setPatentLinks((prev) => prev.filter((link) => link.link_id !== linkId));
      } else {
        await reviewCompanyProductLink(
          linkId,
          decision,
          reviewedBy.trim() || undefined,
          note
        );
        setCompanyProductLinks((prev) => prev.filter((link) => link.link_id !== linkId));
      }
      setNotes((prev) => {
        const next = { ...prev };
        delete next[linkId];
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新に失敗しました");
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>レビューキュー</CardTitle>
          <CardDescription>確定前のリンクを承認/却下できます</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="reviewedBy" className="mb-1 block">
              レビュー担当者
            </Label>
            <Input
              id="reviewedBy"
              name="reviewedBy"
              value={reviewedBy}
              onChange={(e) => setReviewedBy(e.target.value)}
              placeholder="例: 田中"
            />
          </div>
          <p className="text-sm text-muted-foreground">
            未レビュー: {totalLinks} 件
          </p>
          <Button onClick={loadQueue} disabled={loading}>
            {loading ? "更新中..." : "キューを更新"}
          </Button>
          {error && (
            <Alert variant="destructive">
              <AlertTitle>エラー</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>特許↔会社リンク</CardTitle>
          <CardDescription>出願人・権利者などのリンク</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {patentLinks.length === 0 && (
            <p className="text-sm text-muted-foreground">レビュー対象はありません</p>
          )}
          {patentLinks.map((link) => (
            <div key={link.link_id} className="rounded border p-3 text-sm space-y-2">
              <div className="font-medium">リンクID: {link.link_id}</div>
              <div className="text-muted-foreground">
                会社ID: {link.company_id}
              </div>
              <div className="text-muted-foreground">
                特許: {link.patent_ref || link.document_id || "-"}
              </div>
              <div className="text-muted-foreground">役割: {link.role}</div>
              {link.confidence_score !== null && (
                <div className="text-muted-foreground">信頼度: {link.confidence_score}</div>
              )}
              <div>
                <Label htmlFor={`note-patent-${link.link_id}`} className="mb-1 block text-xs">
                  レビュー理由
                </Label>
                <Input
                  id={`note-patent-${link.link_id}`}
                  name={`note-patent-${link.link_id}`}
                  value={notes[link.link_id] || ""}
                  onChange={(e) =>
                    setNotes((prev) => ({ ...prev, [link.link_id]: e.target.value }))
                  }
                  placeholder="例: 住所一致のため承認"
                />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={() => handleReview("patent", link.link_id, "approve")}>
                  承認
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleReview("patent", link.link_id, "reject")}
                >
                  却下
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>会社↔製品リンク</CardTitle>
          <CardDescription>製造元・販売元などのリンク</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {companyProductLinks.length === 0 && (
            <p className="text-sm text-muted-foreground">レビュー対象はありません</p>
          )}
          {companyProductLinks.map((link) => (
            <div key={link.link_id} className="rounded border p-3 text-sm space-y-2">
              <div className="font-medium">リンクID: {link.link_id}</div>
              <div className="text-muted-foreground">
                会社ID: {link.company_id}
              </div>
              <div className="text-muted-foreground">
                製品ID: {link.product_id || "-"}
              </div>
              <div className="text-muted-foreground">役割: {link.role}</div>
              {link.confidence_score !== null && (
                <div className="text-muted-foreground">信頼度: {link.confidence_score}</div>
              )}
              <div>
                <Label htmlFor={`note-product-${link.link_id}`} className="mb-1 block text-xs">
                  レビュー理由
                </Label>
                <Input
                  id={`note-product-${link.link_id}`}
                  name={`note-product-${link.link_id}`}
                  value={notes[link.link_id] || ""}
                  onChange={(e) =>
                    setNotes((prev) => ({ ...prev, [link.link_id]: e.target.value }))
                  }
                  placeholder="例: 公式サイト一致のため承認"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleReview("company-product", link.link_id, "approve")}
                >
                  承認
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleReview("company-product", link.link_id, "reject")}
                >
                  却下
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
