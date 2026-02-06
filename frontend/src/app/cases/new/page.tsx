"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { createCase } from "@/lib/api";

export default function NewCasePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [patentId, setPatentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!title.trim()) {
      setError("案件名を入力してください。");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await createCase({
        title: title.trim(),
        description: description.trim() || undefined,
        patent_id: patentId.trim() || undefined,
      });
      router.push(`/cases/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "案件の作成に失敗しました");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link href="/cases" className="text-blue-600 hover:text-blue-800 text-sm">
          &larr; 案件一覧に戻る
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>新規案件作成</CardTitle>
          <CardDescription>
            特許侵害調査の案件を作成します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title" className="mb-2 block">
                案件名 *
              </Label>
              <Input
                id="title"
                placeholder="例: A社製品群の侵害調査"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={loading}
              />
            </div>

            <div>
              <Label htmlFor="description" className="mb-2 block">
                説明
              </Label>
              <Textarea
                id="description"
                placeholder="案件の概要や目的を記入"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={loading}
                className="min-h-[100px]"
              />
            </div>

            <div>
              <Label htmlFor="patentId" className="mb-2 block">
                対象特許 (内部UUID, オプション)
              </Label>
              <Input
                id="patentId"
                placeholder="特許の内部ID (UUID形式)"
                value={patentId}
                onChange={(e) => setPatentId(e.target.value)}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground mt-1">
                後から案件詳細ページで追加することもできます
              </p>
            </div>

            {error && (
              <p className="text-sm text-red-600">{error}</p>
            )}

            <div className="flex justify-end gap-2">
              <Link href="/cases">
                <Button variant="outline" disabled={loading}>
                  キャンセル
                </Button>
              </Link>
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? "作成中..." : "案件を作成"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
