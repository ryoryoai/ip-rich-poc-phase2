"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  createKeyword,
  searchKeywords,
  type KeywordSearchResult,
} from "@/lib/api";

type KeywordFormState = {
  term: string;
  language: string;
  synonyms: string;
  abbreviations: string;
  domain: string;
  notes: string;
};

export default function KeywordMasterPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLanguage, setSearchLanguage] = useState("");
  const [searchResults, setSearchResults] = useState<KeywordSearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const [form, setForm] = useState<KeywordFormState>({
    term: "",
    language: "ja",
    synonyms: "",
    abbreviations: "",
    domain: "",
    notes: "",
  });
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const handleSearch = async () => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const results = await searchKeywords(searchQuery.trim(), searchLanguage.trim() || undefined);
      setSearchResults(results);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "検索に失敗しました");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleCreate = async () => {
    setCreateLoading(true);
    setCreateError(null);
    setCreateMessage(null);
    try {
      const payload = {
        term: form.term.trim(),
        language: form.language.trim() || undefined,
        synonyms: form.synonyms
          ? form.synonyms.split(",").map((v) => v.trim()).filter(Boolean)
          : undefined,
        abbreviations: form.abbreviations
          ? form.abbreviations.split(",").map((v) => v.trim()).filter(Boolean)
          : undefined,
        domain: form.domain.trim() || undefined,
        notes: form.notes.trim() || undefined,
      };
      const result = await createKeyword(payload);
      setCreateMessage(
        result.existing
          ? `既存キーワードを取得しました: ${result.keyword_id}`
          : `キーワードを作成しました: ${result.keyword_id}`
      );
      setForm({
        term: "",
        language: "ja",
        synonyms: "",
        abbreviations: "",
        domain: "",
        notes: "",
      });
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "作成に失敗しました");
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>キーワード検索</CardTitle>
          <CardDescription>
            技術用語・同義語を検索できます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Input
              placeholder="例: エッジAI"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Input
              placeholder="言語 (ja/en)"
              value={searchLanguage}
              onChange={(e) => setSearchLanguage(e.target.value)}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? "検索中..." : "検索"}
            </Button>
          </div>
          {searchError && <p className="text-sm text-red-600">{searchError}</p>}
          {searchResults.length > 0 && (
            <div className="space-y-2">
              {searchResults.map((item) => (
                <div key={item.keyword_id} className="rounded border p-3 text-sm">
                  <div className="font-medium">{item.term}</div>
                  <div className="text-muted-foreground">
                    言語: {item.language} / ID: {item.keyword_id}
                  </div>
                  {item.domain && (
                    <div className="text-muted-foreground">領域: {item.domain}</div>
                  )}
                  {item.synonyms.length > 0 && (
                    <div className="text-muted-foreground">
                      同義語: {item.synonyms.join(", ")}
                    </div>
                  )}
                  {item.abbreviations.length > 0 && (
                    <div className="text-muted-foreground">
                      略語: {item.abbreviations.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>キーワード登録</CardTitle>
          <CardDescription>
            海外探索向けの用語と同義語を追加できます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="keywordTerm" className="mb-1 block">
                用語
              </Label>
              <Input
                id="keywordTerm"
                name="keywordTerm"
                value={form.term}
                onChange={(e) => setForm({ ...form, term: e.target.value })}
                placeholder="例: エッジAI / Edge AI"
              />
            </div>
            <div>
              <Label htmlFor="keywordLanguage" className="mb-1 block">
                言語
              </Label>
              <Input
                id="keywordLanguage"
                name="keywordLanguage"
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value })}
                placeholder="ja"
              />
            </div>
            <div>
              <Label htmlFor="keywordDomain" className="mb-1 block">
                領域
              </Label>
              <Input
                id="keywordDomain"
                name="keywordDomain"
                value={form.domain}
                onChange={(e) => setForm({ ...form, domain: e.target.value })}
                placeholder="例: 画像処理"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="keywordSynonyms" className="mb-1 block">
                同義語（カンマ区切り）
              </Label>
              <Input
                id="keywordSynonyms"
                name="keywordSynonyms"
                value={form.synonyms}
                onChange={(e) => setForm({ ...form, synonyms: e.target.value })}
                placeholder="例: エッジ人工知能, Edge Intelligence"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="keywordAbbreviations" className="mb-1 block">
                略語（カンマ区切り）
              </Label>
              <Input
                id="keywordAbbreviations"
                name="keywordAbbreviations"
                value={form.abbreviations}
                onChange={(e) => setForm({ ...form, abbreviations: e.target.value })}
                placeholder="例: EAI"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="keywordNotes" className="mb-1 block">
                メモ
              </Label>
              <Textarea
                id="keywordNotes"
                name="keywordNotes"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="探索時の注意点や表記揺れ"
              />
            </div>
          </div>

          {createError && <p className="text-sm text-red-600">{createError}</p>}
          {createMessage && <p className="text-sm text-green-700">{createMessage}</p>}

          <div className="flex justify-end">
            <Button onClick={handleCreate} disabled={createLoading}>
              {createLoading ? "保存中..." : "キーワードを登録"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
