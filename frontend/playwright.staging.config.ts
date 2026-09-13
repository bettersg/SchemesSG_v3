import { defineConfig, devices } from "@playwright/test";
import { STAGING_ORIGIN } from "./staging-smoke/read-only-network";

export default defineConfig({
  testDir: "./staging-smoke",
  testMatch: "**/*.spec.ts",
  updateSnapshots: "none",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report/staging" }],
  ],
  outputDir: "test-results/staging",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    ...devices["Desktop Chrome"],
    baseURL: STAGING_ORIGIN,
    colorScheme: "light",
    contextOptions: {
      reducedMotion: "reduce",
    },
    locale: "en-SG",
    screenshot: "only-on-failure",
    serviceWorkers: "block",
    timezoneId: "Asia/Singapore",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "staging-availability",
      testMatch: "availability.spec.ts",
    },
    {
      name: "staging-product",
      testMatch: "product.spec.ts",
      dependencies: ["staging-availability"],
    },
  ],
});
