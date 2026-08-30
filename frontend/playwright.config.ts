import { defineConfig, devices } from "@playwright/test";
import {
  E2E_API_ORIGIN,
  E2E_FIREBASE_CONFIG,
} from "./e2e/fixtures/landing-results";

const baseURL = "http://127.0.0.1:3100";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  outputDir: "test-results",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL,
    colorScheme: "light",
    contextOptions: {
      reducedMotion: "reduce",
    },
    locale: "en-SG",
    screenshot: "only-on-failure",
    serviceWorkers: "block",
    timezoneId: "Asia/Singapore",
    trace: process.env.CI ? "on-first-retry" : "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      testIgnore: "**/mobile-*.spec.ts",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: "mobile-narrow-chromium",
      testMatch: "**/mobile-*.spec.ts",
      use: {
        ...devices["Pixel 10"],
      },
    },
  ],
  webServer: {
    command:
      "npm run dev -- --webpack --hostname 127.0.0.1 --port 3100",
    env: {
      NEXT_PUBLIC_API_BASE_URL: E2E_API_ORIGIN,
      NEXT_PUBLIC_FB_API_KEY: E2E_FIREBASE_CONFIG.apiKey,
      NEXT_PUBLIC_FIREBASE_APP_ID: E2E_FIREBASE_CONFIG.appId,
      NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID:
        E2E_FIREBASE_CONFIG.measurementId,
      NEXT_PUBLIC_FIREBASE_PROJECT_ID: E2E_FIREBASE_CONFIG.projectId,
      NEXT_TELEMETRY_DISABLED: "1",
    },
    reuseExistingServer: false,
    stderr: "pipe",
    stdout: "ignore",
    timeout: 120_000,
    url: baseURL,
  },
});
