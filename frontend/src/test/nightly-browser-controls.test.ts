import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import nightlyConfig from "../../playwright.nightly.config";
import stagingConfig from "../../playwright.staging.config";
import { STAGING_ORIGIN } from "../../staging-smoke/read-only-network";

function projectByName(
  config: typeof nightlyConfig | typeof stagingConfig,
  name: string,
) {
  return config.projects?.find((project) => project.name === name);
}

describe("nightly browser controls", () => {
  it("runs the desktop smoke journeys across all three browser engines", () => {
    expect(nightlyConfig.projects?.map((project) => project.name)).toEqual([
      "chromium",
      "firefox",
      "webkit",
    ]);
    expect(projectByName(nightlyConfig, "chromium")?.ignoreSnapshots).not.toBe(
      true,
    );
    expect(projectByName(nightlyConfig, "firefox")?.ignoreSnapshots).toBe(true);
    expect(projectByName(nightlyConfig, "webkit")?.ignoreSnapshots).toBe(true);
    expect(nightlyConfig.updateSnapshots).toBe("none");
    expect(nightlyConfig.testIgnore).toBe("dev-smoke/**");
  });

  it("runs only on a schedule or manual dispatch with bounded artifacts", () => {
    const workflowPath = resolve(
      process.cwd(),
      "../.github/workflows/nightly-browser.yml",
    );
    const workflow = readFileSync(workflowPath, "utf8");

    expect(workflow).toMatch(/^  schedule:$/m);
    expect(workflow).toMatch(/^  workflow_dispatch:$/m);
    expect(workflow).not.toMatch(/^  pull_request:$/m);
    expect(workflow).toContain("browser: [chromium, firefox, webkit]");
    expect(workflow).toContain("retention-days: 7");
    expect(workflow).not.toContain("secrets.");
    expect(workflow.match(/timeout --kill-after=10s 120s/g)).toHaveLength(3);
    expect(workflow).toContain("Staging availability/configuration failed");
    expect(workflow).toContain("Staging product assertions failed");
    const errorAnnotations = workflow
      .split("\n")
      .filter((line) => line.includes("::error title="));
    expect(errorAnnotations).toHaveLength(6);
    expect(errorAnnotations.every((line) => line.includes("Run '"))).toBe(true);
  });
});

describe("deployed staging smoke controls", () => {
  it("routes availability failures through read-only browser diagnostics", () => {
    const availabilitySpec = readFileSync(
      resolve(process.cwd(), "staging-smoke/availability.spec.ts"),
      "utf8",
    );
    const readOnlyFixture = readFileSync(
      resolve(process.cwd(), "staging-smoke/read-only-fixture.ts"),
      "utf8",
    );
    const workflow = readFileSync(
      resolve(process.cwd(), "../.github/workflows/nightly-browser.yml"),
      "utf8",
    );

    expect(availabilitySpec).toContain('from "./read-only-fixture"');
    expect(availabilitySpec).toContain("page.goto");
    expect(availabilitySpec).toContain("page.evaluate");
    expect(availabilitySpec).not.toContain("request.get");
    expect(availabilitySpec).toContain(
      "staging page referenced a script outside development hosting",
    );
    expect(readOnlyFixture).toContain("allowedRequests");
    expect(readOnlyFixture).toContain("blockedRequests");
    expect(readOnlyFixture).toContain("read-only-network-guard.json");
    expect(stagingConfig.use?.screenshot).toBe("only-on-failure");
    expect(stagingConfig.use?.trace).toBe("retain-on-failure");
    expect(stagingConfig.outputDir).toBe("test-results/staging");
    expect(workflow).toContain("frontend/playwright-report/staging/");
    expect(workflow).toContain("frontend/test-results/staging/");
  });

  it("separates availability/configuration from product assertions", () => {
    expect(stagingConfig.use?.baseURL).toBe(STAGING_ORIGIN);
    expect(stagingConfig.webServer).toBeUndefined();
    expect(stagingConfig.projects?.map((project) => project.name)).toEqual([
      "staging-availability",
      "staging-product",
    ]);
    expect(
      projectByName(stagingConfig, "staging-product")?.dependencies,
    ).toEqual(["staging-availability"]);
  });
});
