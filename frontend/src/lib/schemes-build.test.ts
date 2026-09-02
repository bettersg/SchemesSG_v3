import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { catalogScheme } from "@/test/fixtures/catalog";

const fetchWithAuth = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({ fetchWithAuth }));

import { getSchemesForSitemap } from "./schemes";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

const catalogPage = (
  schemes: Array<Record<string, unknown>>,
  nextCursor?: string,
) =>
  Response.json({
    data: schemes,
    total_count: schemes.length,
    has_more: Boolean(nextCursor),
    next_cursor: nextCursor,
  });

beforeEach(() => {
  fetchWithAuth.mockReset();
});

afterEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = configuredApiUrl;
});

describe("sitemap scheme loading", () => {
  it("skips remote loading when the API URL is not configured", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    await expect(getSchemesForSitemap()).resolves.toEqual([]);
    expect(fetchWithAuth).not.toHaveBeenCalled();
  });

  it("follows the catalog cursor until the last page and de-duplicates", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
    fetchWithAuth
      .mockResolvedValueOnce(
        catalogPage(
          [{ ...catalogScheme, scheme_id: "page-1-scheme" }],
          "cursor-2",
        ),
      )
      .mockResolvedValueOnce(
        catalogPage([
          { ...catalogScheme, scheme_id: "page-2-scheme" },
          // The same scheme reappearing across pages must not be emitted twice.
          { ...catalogScheme, scheme_id: "page-1-scheme" },
        ]),
      );

    const schemes = await getSchemesForSitemap();

    expect(schemes.map((scheme) => scheme.schemeId)).toEqual([
      "page-1-scheme",
      "page-2-scheme",
    ]);
    expect(fetchWithAuth).toHaveBeenCalledTimes(2);
    expect(fetchWithAuth.mock.calls[0][0]).toBe(
      "https://api.test/catalog?limit=200",
    );
    expect(fetchWithAuth.mock.calls[1][0]).toBe(
      "https://api.test/catalog?limit=200&cursor=cursor-2",
    );
  });

  it("omits schemes the search path kept unlisted", async () => {
    // /catalog only filters retired schemes; the sitemap must also drop inactive
    // ones, as the search it replaced did.
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
    fetchWithAuth.mockResolvedValueOnce(
      catalogPage([
        { ...catalogScheme, scheme_id: "listed-scheme", status: "active" },
        { ...catalogScheme, scheme_id: "unlisted-scheme", status: "inactive" },
        { ...catalogScheme, scheme_id: "gone-scheme", status: "retired" },
      ]),
    );

    const schemes = await getSchemesForSitemap();

    expect(schemes.map((scheme) => scheme.schemeId)).toEqual(["listed-scheme"]);
  });

  it("keeps the pages already collected when a later page fails", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
    fetchWithAuth
      .mockResolvedValueOnce(
        catalogPage([{ ...catalogScheme, scheme_id: "kept-scheme" }], "cursor-2"),
      )
      .mockResolvedValueOnce(new Response(null, { status: 500 }));

    const schemes = await getSchemesForSitemap();

    expect(schemes.map((scheme) => scheme.schemeId)).toEqual(["kept-scheme"]);
  });

  it("keeps the pages already collected when a page throws", async () => {
    // A build-time network failure must not take the static sitemap routes down.
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    fetchWithAuth
      .mockResolvedValueOnce(
        catalogPage(
          [{ ...catalogScheme, scheme_id: "kept-scheme" }],
          "cursor-2",
        ),
      )
      .mockRejectedValueOnce(new Error("getaddrinfo ENOTFOUND api.test"));

    const schemes = await getSchemesForSitemap();

    expect(schemes.map((scheme) => scheme.schemeId)).toEqual(["kept-scheme"]);
    vi.restoreAllMocks();
  });

  it("returns no schemes when the first page fails", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
    fetchWithAuth.mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(getSchemesForSitemap()).resolves.toEqual([]);
  });
});
