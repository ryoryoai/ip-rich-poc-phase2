import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for e2e tests
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Cronジョブのテストは順番に実行
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // DB操作があるため並列実行は避ける
  reporter: 'list',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3001',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    port: 3001,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});