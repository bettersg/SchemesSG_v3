import { afterEach, describe, expect, it, vi } from "vitest";

const fetchWithAuth = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({ fetchWithAuth }));

import { getSchemesForSitemap } from "./schemes";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

afterEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = configuredApiUrl;
});

describe("sitemap scheme loading", () => {
  it("skips remote loading when the API URL is not configured", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    await expect(getSchemesForSitemap()).resolves.toEqual([]);
    expect(fetchWithAuth).not.toHaveBeenCalled();
  });
});
