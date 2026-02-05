import { test, expect } from "@playwright/test";

test("company master search and create", async ({ page }) => {
  await page.route("**/api/v1/companies/search**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            company_id: "c-001",
            name: "株式会社テスト",
            corporate_number: "1234567890123",
            normalized_name: "テスト",
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/companies", async (route) => {
    if (route.request().method() !== "POST") {
      return route.fallback();
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        company_id: "c-002",
        name: "株式会社サンプル",
        corporate_number: "1111222233334",
        normalized_name: "サンプル",
        existing: false,
      }),
    });
  });

  await page.goto("/master/companies");

  await page.getByPlaceholder("例: 株式会社テスト、1234567890123").fill("テスト");
  await page.getByRole("button", { name: "検索" }).first().click();
  await expect(page.getByText("株式会社テスト")).toBeVisible();

  await page.getByLabel("会社名").fill("株式会社サンプル");
  await page.getByLabel("法人番号").fill("1111222233334");
  await page.getByRole("button", { name: "会社を登録" }).click();

  await expect(page.getByText("会社を作成しました: c-002")).toBeVisible();
});

test("product master search and create", async ({ page }) => {
  await page.route("**/api/v1/companies/search**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            company_id: "c-010",
            name: "株式会社プロダクト",
            corporate_number: "9876543210987",
            normalized_name: "プロダクト",
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/products/search**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        results: [
          {
            product_id: "p-001",
            company_id: "c-010",
            name: "テスト装置",
            model_number: "X-100",
            normalized_name: "テスト装置",
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/products", async (route) => {
    if (route.request().method() !== "POST") {
      return route.fallback();
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        product_id: "p-002",
        name: "テスト装置",
        model_number: "X-100",
        normalized_name: "テスト装置",
        existing: false,
      }),
    });
  });

  await page.goto("/master/products");

  await page.getByPlaceholder("会社名または法人番号").fill("プロダクト");
  await page.getByRole("button", { name: "検索" }).first().click();
  await page.getByRole("button", { name: "この会社IDを使用" }).click();

  await page.getByLabel("製品名").fill("テスト装置");
  await page.getByLabel("型番").fill("X-100");
  await page.getByRole("button", { name: "製品を登録" }).click();

  await expect(page.getByText("製品を作成しました: p-002")).toBeVisible();

  await page.getByPlaceholder("例: Model X, 123-ABC").fill("X-100");
  await page.getByRole("button", { name: "検索" }).nth(1).click();
  await expect(page.getByText("テスト装置")).toBeVisible();
});

test("review queue approve", async ({ page }) => {
  await page.route("**/api/v1/links/review-queue**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        patent_company_links: [
          {
            link_id: "l-001",
            company_id: "c-100",
            patent_ref: "JP1234567B2",
            role: "assignee",
            link_type: "probabilistic",
            confidence_score: 75,
            review_status: "pending",
          },
        ],
        company_product_links: [
          {
            link_id: "l-002",
            company_id: "c-200",
            product_id: "p-200",
            role: "manufacturer",
            link_type: "probabilistic",
            confidence_score: 60,
            review_status: "pending",
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/links/patent-company/*/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        link_id: "l-001",
        review_status: "approved",
        link_type: "deterministic",
      }),
    });
  });

  await page.route("**/api/v1/links/company-product/*/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        link_id: "l-002",
        review_status: "approved",
        link_type: "deterministic",
      }),
    });
  });

  await page.goto("/master/review");

  await expect(page.getByText("リンクID: l-001")).toBeVisible();
  await page.getByRole("button", { name: "承認" }).first().click();
  await expect(page.getByText("リンクID: l-001")).toHaveCount(0);

  await expect(page.getByText("リンクID: l-002")).toBeVisible();
  await page.getByRole("button", { name: "承認" }).first().click();
  await expect(page.getByText("リンクID: l-002")).toHaveCount(0);
});
