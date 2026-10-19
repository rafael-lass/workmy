import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: process.env.LIVE_SMOKE === 'true' ? 'live.spec.mjs' : 'cloud.spec.mjs',
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  use: {
    baseURL: process.env.APP_URL || 'https://localhost:8443',
    ignoreHTTPSErrors: process.env.LIVE_SMOKE !== 'true',
    // Authenticated live checks must not produce traces with session secrets.
    trace: process.env.LIVE_SMOKE === 'true' ? 'off' : 'retain-on-failure',
    browserName: 'chromium',
    channel: process.env.PLAYWRIGHT_CHANNEL || 'chromium',
  },
  reporter: [['list'], ['html', { open: 'never' }]],
});
