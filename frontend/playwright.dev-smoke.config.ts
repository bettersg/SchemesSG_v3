import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e/dev-smoke",
  testMatch: "dev-search-smoke.spec.ts",
  timeout: 120_000,
  expect: { timeout: 90_000 },
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-dev-smoke-report" }]],
  outputDir: "test-results/dev-smoke",
  use: {
    baseURL: process.env.DEV_SMOKE_BASE_URL ?? "http://localhost:3000",
    locale: "en-SG",
    timezoneId: "Asia/Singapore",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  workers: 1,
});
