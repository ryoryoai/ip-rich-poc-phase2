"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  createCompany,
  searchCompanies,
  type CompanySearchResult,
} from "@/lib/api";

type CompanyFormState = {
  name: string;
  corporate_number: string;
  country: string;
  legal_type: string;
  address_raw: string;
  address_pref: string;
  address_city: string;
  status: string;
  business_description: string;
  primary_products: string;
  market_regions: string;
  website_url: string;
  contact_url: string;
  aliases: string;
};

export default function CompanyMasterPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<CompanySearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const [form, setForm] = useState<CompanyFormState>({
    name: "",
    corporate_number: "",
    country: "",
    legal_type: "",
    address_raw: "",
    address_pref: "",
    address_city: "",
    status: "",
    business_description: "",
    primary_products: "",
    market_regions: "",
    website_url: "",
    contact_url: "",
    aliases: "",
  });
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const handleSearch = async () => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const results = await searchCompanies(searchQuery.trim());
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
        ...form,
        corporate_number: form.corporate_number?.trim() || undefined,
        country: form.country?.trim() || undefined,
        legal_type: form.legal_type?.trim() || undefined,
        address_raw: form.address_raw?.trim() || undefined,
        address_pref: form.address_pref?.trim() || undefined,
        address_city: form.address_city?.trim() || undefined,
        status: form.status?.trim() || undefined,
        business_description: form.business_description?.trim() || undefined,
        primary_products: form.primary_products?.trim() || undefined,
        market_regions: form.market_regions?.trim() || undefined,
        website_url: form.website_url?.trim() || undefined,
        contact_url: form.contact_url?.trim() || undefined,
        aliases: form.aliases
          ? form.aliases
              .split(",")
              .map((alias) => alias.trim())
              .filter(Boolean)
          : undefined,
      };
      const result = await createCompany(payload);
      setCreateMessage(
        result.existing
          ? `既存会社を取得しました: ${result.company_id}`
          : `会社を作成しました: ${result.company_id}`
      );
      setForm({
        name: "",
        corporate_number: "",
        country: "",
        legal_type: "",
        address_raw: "",
        address_pref: "",
        address_city: "",
        status: "",
        business_description: "",
        primary_products: "",
        market_regions: "",
        website_url: "",
        contact_url: "",
        aliases: "",
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
          <CardTitle>会社検索</CardTitle>
          <CardDescription>
            会社名・別名・法人番号で検索できます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="例: 株式会社テスト、1234567890123"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              {searchLoading ? "検索中..." : "検索"}
            </Button>
          </div>
          {searchError && <p className="text-sm text-red-600">{searchError}</p>}
          {searchResults.length > 0 && (
            <div className="space-y-2">
              {searchResults.map((company) => (
                <div
                  key={company.company_id}
                  className="rounded border border-muted p-3 text-sm"
                >
                  <div className="font-medium">{company.name}</div>
                  <div className="text-muted-foreground">
                    ID: {company.company_id}
                  </div>
                  {company.corporate_number && (
                    <div className="text-muted-foreground">
                      法人番号: {company.corporate_number}
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
          <CardTitle>会社の登録</CardTitle>
          <CardDescription>
            法人番号がある場合は13桁で入力してください
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="companyName" className="mb-1 block">
                会社名
              </Label>
              <Input
                id="companyName"
                name="companyName"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例: 株式会社テスト"
              />
            </div>
            <div>
              <Label htmlFor="corporateNumber" className="mb-1 block">
                法人番号
              </Label>
              <Input
                id="corporateNumber"
                name="corporateNumber"
                value={form.corporate_number}
                onChange={(e) =>
                  setForm({ ...form, corporate_number: e.target.value })
                }
                placeholder="13桁"
              />
            </div>
            <div>
              <Label htmlFor="companyCountry" className="mb-1 block">
                国
              </Label>
              <Input
                id="companyCountry"
                name="companyCountry"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                placeholder="例: JP"
              />
            </div>
            <div>
              <Label htmlFor="companyLegalType" className="mb-1 block">
                法人種別
              </Label>
              <Input
                id="companyLegalType"
                name="companyLegalType"
                value={form.legal_type}
                onChange={(e) => setForm({ ...form, legal_type: e.target.value })}
                placeholder="例: 株式会社"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="companyAddressRaw" className="mb-1 block">
                住所（原文）
              </Label>
              <Textarea
                id="companyAddressRaw"
                name="companyAddressRaw"
                value={form.address_raw}
                onChange={(e) => setForm({ ...form, address_raw: e.target.value })}
                placeholder="例: 東京都千代田区..."
              />
            </div>
            <div>
              <Label htmlFor="companyPref" className="mb-1 block">
                都道府県
              </Label>
              <Input
                id="companyPref"
                name="companyPref"
                value={form.address_pref}
                onChange={(e) => setForm({ ...form, address_pref: e.target.value })}
                placeholder="例: 東京都"
              />
            </div>
            <div>
              <Label htmlFor="companyCity" className="mb-1 block">
                市区町村
              </Label>
              <Input
                id="companyCity"
                name="companyCity"
                value={form.address_city}
                onChange={(e) => setForm({ ...form, address_city: e.target.value })}
                placeholder="例: 千代田区"
              />
            </div>
            <div>
              <Label htmlFor="companyWebsite" className="mb-1 block">
                Webサイト
              </Label>
              <Input
                id="companyWebsite"
                name="companyWebsite"
                value={form.website_url}
                onChange={(e) => setForm({ ...form, website_url: e.target.value })}
                placeholder="https://example.com"
              />
            </div>
            <div>
              <Label htmlFor="companyContact" className="mb-1 block">
                問い合わせURL
              </Label>
              <Input
                id="companyContact"
                name="companyContact"
                value={form.contact_url}
                onChange={(e) => setForm({ ...form, contact_url: e.target.value })}
                placeholder="https://example.com/contact"
              />
            </div>
            <div>
              <Label htmlFor="companyStatus" className="mb-1 block">
                ステータス
              </Label>
              <Input
                id="companyStatus"
                name="companyStatus"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                placeholder="例: active"
              />
            </div>
            <div>
              <Label htmlFor="companyMarketRegions" className="mb-1 block">
                市場（国・地域）
              </Label>
              <Input
                id="companyMarketRegions"
                name="companyMarketRegions"
                value={form.market_regions}
                onChange={(e) => setForm({ ...form, market_regions: e.target.value })}
                placeholder="例: JP, US, EU"
              />
            </div>
            <div>
              <Label htmlFor="companyAliases" className="mb-1 block">
                別名（カンマ区切り）
              </Label>
              <Input
                id="companyAliases"
                name="companyAliases"
                value={form.aliases}
                onChange={(e) => setForm({ ...form, aliases: e.target.value })}
                placeholder="例: (株)テスト, Test Inc."
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="companyPrimaryProducts" className="mb-1 block">
                主要製品（カンマ区切り）
              </Label>
              <Input
                id="companyPrimaryProducts"
                name="companyPrimaryProducts"
                value={form.primary_products}
                onChange={(e) => setForm({ ...form, primary_products: e.target.value })}
                placeholder="例: 製品A, 製品B"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="companyBusinessDescription" className="mb-1 block">
                事業内容
              </Label>
              <Textarea
                id="companyBusinessDescription"
                name="companyBusinessDescription"
                value={form.business_description}
                onChange={(e) => setForm({ ...form, business_description: e.target.value })}
                placeholder="事業内容やサービス概要"
              />
            </div>
          </div>

          {createError && <p className="text-sm text-red-600">{createError}</p>}
          {createMessage && (
            <p className="text-sm text-green-700">{createMessage}</p>
          )}

          <div className="flex justify-end">
            <Button onClick={handleCreate} disabled={createLoading}>
              {createLoading ? "保存中..." : "会社を登録"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
