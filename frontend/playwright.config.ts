import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  expect: { timeout: 8000 },
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5174',
    viewport: { width: 1440, height: 1000 },
    channel: 'chrome',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: [
    {
      command: '../.venv/bin/python tests/start_backend.py',
      url: 'http://127.0.0.1:8001/api/v1/health',
      reuseExistingServer: false,
      timeout: 60000,
    },
    {
      command: 'npm run dev -- --port 5174',
      url: 'http://127.0.0.1:5174',
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:8001/api/v1' },
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
