import { test, expect } from '@playwright/test';

// Phase1 migrated job ID
const PHASE1_JOB_ID = '147c5e7d-cb33-48ce-a3bc-5c60a5bd61a5';

test.describe('Phase1 Migration Data', () => {
  test('job list shows Phase1 migrated jobs', async ({ page }) => {
    await page.goto('/research/list');

    // Wait for the page to load
    await expect(page.getByRole('heading', { name: '分析履歴一覧' })).toBeVisible();

    // Wait for data to load
    await page.waitForTimeout(2000);

    // Look for Phase1 pipeline marker (card-based layout)
    const phase1Cell = page.locator('text=phase1').first();
    await expect(phase1Cell).toBeVisible();

    // Check that patent numbers are displayed
    await expect(page.locator('text=6718962').first()).toBeVisible();
  });

  test('job detail page loads Phase1 data', async ({ page }) => {
    await page.goto(`/research/result/${PHASE1_JOB_ID}`);

    // Wait for loading to complete
    await page.waitForSelector('text=分析結果', { timeout: 10000 });

    // Check job info is displayed
    await expect(page.locator('text=特許番号')).toBeVisible();
    await expect(page.locator('text=7666636')).toBeVisible();

    // Check pipeline shows phase1
    await expect(page.locator('text=phase1')).toBeVisible();

    // Check that results are displayed (not "結果がありません")
    const noResults = page.locator('text=結果がありません');
    await expect(noResults).not.toBeVisible();

    // Check deep_research stage is present
    await expect(page.locator('text=deep_research')).toBeVisible();
  });

  test('job detail shows expandable stage results', async ({ page }) => {
    await page.goto(`/research/result/${PHASE1_JOB_ID}`);

    // Wait for the page to load
    await page.waitForSelector('text=deep_research', { timeout: 10000 });

    // Click on the deep_research stage to expand
    const stageHeader = page.locator('text=deep_research').first();
    await stageHeader.click();

    // After expanding, should see JSON content (pre tag)
    const preContent = page.locator('pre');
    await expect(preContent).toBeVisible();
  });
});
