import { defineConfig, devices } from "@playwright/test";
import baseConfig from "./playwright.config";

export default defineConfig({
  ...baseConfig,
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
      name: "firefox",
      testIgnore: "**/mobile-*.spec.ts",
      ignoreSnapshots: true,
      use: {
        ...devices["Desktop Firefox"],
      },
    },
    {
      name: "webkit",
      testIgnore: "**/mobile-*.spec.ts",
      ignoreSnapshots: true,
      use: {
        ...devices["Desktop Safari"],
      },
    },
  ],
});
