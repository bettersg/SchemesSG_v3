import { afterEach, describe, expect, it, vi } from "vitest";

const configuredProjectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

afterEach(() => {
  process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID = configuredProjectId;
});

/** Re-import after mutating env, since the base URL is a module-level const. */
async function loadBaseUrl(projectId: string | undefined) {
  if (projectId === undefined) {
    delete process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  } else {
    process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID = projectId;
  }
  vi.resetModules();
  return (await import("./partner-api-reference")).PARTNER_API_BASE;
}

describe("partner API base URL", () => {
  it("documents the project the page was built for", async () => {
    await expect(loadBaseUrl("schemessg-v3-dev")).resolves.toBe(
      "https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net/partner_api",
    );
    await expect(loadBaseUrl("schemessg")).resolves.toBe(
      "https://asia-southeast1-schemessg.cloudfunctions.net/partner_api",
    );
  });

  it("falls back to production rather than an undefined host", async () => {
    await expect(loadBaseUrl(undefined)).resolves.toBe(
      "https://asia-southeast1-schemessg.cloudfunctions.net/partner_api",
    );
  });
});
