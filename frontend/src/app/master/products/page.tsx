"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  createProduct,
  searchProducts,
  searchCompanies,
  type ProductSearchResult,
  type CompanySearchResult,
} from "@/lib/api";

type ProductFormState = {
  company_id: string;
  name: string;
  model_number: string;
  brand_name: string;
  category_path: string;
  description: string;
  sale_region: string;
  status: string;
};

export default function ProductMasterPage() {
  const [companyQuery, setCompanyQuery] = useState("");
  const [companyResults, setCompanyResults] = useState<CompanySearchResult[]>([]);
  const [companyError, setCompanyError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const [form, setForm] = useState<ProductFormState>({
    company_id: "",
    name: "",
    model_number: "",
    brand_name: "",
    category_path: "",
    description: "",
    sale_region: "",
    status: "",
  });
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createLoading, setCreateLoading] = useState(false);

  const handleCompanySearch = async () => {
    setCompanyError(null);
    try {
      const results = await searchCompanies(companyQuery.trim());
      setCompanyResults(results);
    } catch (err) {
      setCompanyError(err instanceof Error ? err.message : "会社検索に失敗しました");
    }
  };

  const handleSearch = async () => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const results = await searchProducts(searchQuery.trim());
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
        company_id: form.company_id.trim(),
        name: form.name.trim(),
        model_number: form.model_number.trim() || undefined,
        brand_name: form.brand_name.trim() || undefined,
        category_path: form.category_path.trim() || undefined,
        description: form.description.trim() || undefined,
        sale_region: form.sale_region.trim() || undefined,
        status: form.status.trim() || undefined,
      };
      const result = await createProduct(payload);
      setCreateMessage(
        result.existing
          ? `既存製品を取得しました: ${result.product_id}`
          : `製品を作成しました: ${result.product_id}`
      );
      setForm({
        company_id: "",
        name: "",
        model_number: "",
        brand_name: "",
        category_path: "",
        description: "",
        sale_region: "",
        status: "",
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
            会社IDを入力するための簡易検索
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="会社名または法人番号"
              value={companyQuery}
              onChange={(e) => setCompanyQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCompanySearch()}
            />
            <Button onClick={handleCompanySearch}>検索</Button>
          </div>
          {companyError && <p className="text-sm text-red-600">{companyError}</p>}
          {companyResults.length > 0 && (
            <div className="space-y-2">
              {companyResults.map((company) => (
                <div key={company.company_id} className="rounded border p-3 text-sm">
                  <div className="font-medium">{company.name}</div>
                  <div className="text-muted-foreground">ID: {company.company_id}</div>
                  <div className="mt-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setForm({ ...form, company_id: company.company_id })}
                    >
                      この会社IDを使用
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>製品検索</CardTitle>
          <CardDescription>
            製品名・型番・識別子で検索できます
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Input
              placeholder="例: Model X, 123-ABC"
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
              {searchResults.map((product) => (
                <div key={product.product_id} className="rounded border p-3 text-sm">
                  <div className="font-medium">{product.name}</div>
                  <div className="text-muted-foreground">ID: {product.product_id}</div>
                  <div className="text-muted-foreground">
                    会社ID: {product.company_id}
                  </div>
                  {product.model_number && (
                    <div className="text-muted-foreground">
                      型番: {product.model_number}
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
          <CardTitle>製品の登録</CardTitle>
          <CardDescription>
            会社IDを指定して製品を登録します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="productCompanyId" className="mb-1 block">
                会社ID
              </Label>
              <Input
                id="productCompanyId"
                name="productCompanyId"
                value={form.company_id}
                onChange={(e) => setForm({ ...form, company_id: e.target.value })}
                placeholder="会社IDを入力"
              />
            </div>
            <div>
              <Label htmlFor="productName" className="mb-1 block">
                製品名
              </Label>
              <Input
                id="productName"
                name="productName"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="例: 製品X"
              />
            </div>
            <div>
              <Label htmlFor="productModel" className="mb-1 block">
                型番
              </Label>
              <Input
                id="productModel"
                name="productModel"
                value={form.model_number}
                onChange={(e) => setForm({ ...form, model_number: e.target.value })}
                placeholder="例: X-1000"
              />
            </div>
            <div>
              <Label htmlFor="productBrand" className="mb-1 block">
                ブランド
              </Label>
              <Input
                id="productBrand"
                name="productBrand"
                value={form.brand_name}
                onChange={(e) => setForm({ ...form, brand_name: e.target.value })}
                placeholder="例: BrandX"
              />
            </div>
            <div>
              <Label htmlFor="productCategory" className="mb-1 block">
                カテゴリ
              </Label>
              <Input
                id="productCategory"
                name="productCategory"
                value={form.category_path}
                onChange={(e) => setForm({ ...form, category_path: e.target.value })}
                placeholder="例: 家電 > 空調 > エアコン"
              />
            </div>
            <div>
              <Label htmlFor="productRegion" className="mb-1 block">
                販売地域
              </Label>
              <Input
                id="productRegion"
                name="productRegion"
                value={form.sale_region}
                onChange={(e) => setForm({ ...form, sale_region: e.target.value })}
                placeholder="例: JP"
              />
            </div>
            <div>
              <Label htmlFor="productStatus" className="mb-1 block">
                ステータス
              </Label>
              <Input
                id="productStatus"
                name="productStatus"
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                placeholder="例: active"
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="productDescription" className="mb-1 block">
                説明
              </Label>
              <Textarea
                id="productDescription"
                name="productDescription"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="製品説明を入力"
              />
            </div>
          </div>

          {createError && <p className="text-sm text-red-600">{createError}</p>}
          {createMessage && <p className="text-sm text-green-700">{createMessage}</p>}

          <div className="flex justify-end">
            <Button onClick={handleCreate} disabled={createLoading}>
              {createLoading ? "保存中..." : "製品を登録"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
