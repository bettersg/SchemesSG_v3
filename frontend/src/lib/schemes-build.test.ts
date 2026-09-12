import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { catalogScheme } from "@/test/fixtures/catalog";
import type { RawSchemeData } from "@/types/types";

vi.mock("server-only", () => ({}));

import {
  getAllCatalogSchemes,
  getCatalogData,
  getSchemeById,
  getSchemesForSitemap,
} from "./schemes.server";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

const catalogPage = (
  schemes: RawSchemeData[],
  options: { total?: number; nextCursor?: string } = {},
) =>
  Response.json({
    data: schemes,
    total_count: options.total ?? schemes.length,
    has_more: Boolean(options.nextCursor),
    next_cursor: options.nextCursor,
  });

beforeEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = configuredApiUrl;
  vi.unstubAllGlobals();
});

describe("public build-time scheme loading", () => {
  it("fails visibly when the public API URL is not configured", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    await expect(getCatalogData()).rejects.toThrow(
      "Missing NEXT_PUBLIC_API_BASE_URL",
    );
    expect(fetch).not.toHaveBeenCalled();
  });

  it("loads catalog data without a Firebase authorization header", async () => {
    vi.mocked(fetch).mockResolvedValue(catalogPage([catalogScheme]));

    await expect(getCatalogData("Financial Assistance")).resolves.toMatchObject(
      {
        schemes: [expect.objectContaining({ schemeId: "test-support-scheme" })],
        total: 1,
        nextCursor: "",
      },
    );

    const [url, init] = vi.mocked(fetch).mock.calls[0];
    expect(String(url)).toBe(
      "https://api.test/catalog?limit=20&category=Financial+Assistance",
    );
    expect(new Headers(init?.headers).has("Authorization")).toBe(false);
  });

  it("loads full scheme details without a Firebase authorization header", async () => {
    vi.mocked(fetch).mockResolvedValue(
      Response.json({ data: { ...catalogScheme, scheme_id: "detail/id" } }),
    );

    await expect(getSchemeById("detail/id")).resolves.toMatchObject({
      schemeId: "detail/id",
    });

    const [url, init] = vi.mocked(fetch).mock.calls[0];
    expect(String(url)).toBe("https://api.test/schemes/detail%2Fid");
    expect(new Headers(init?.headers).has("Authorization")).toBe(false);
  });

  it("surfaces an actionable public scheme-detail API error", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response("upstream unavailable", { status: 503 }),
    );

    await expect(getSchemeById("failed-scheme")).rejects.toThrow(
      "Unable to fetch scheme failed-scheme (503): upstream unavailable",
    );
  });

  it("enumerates every catalog page and de-duplicates scheme ids", async () => {
    const firstPage = Array.from({ length: 20 }, (_, index) => ({
      ...catalogScheme,
      scheme_id: `page-1-scheme-${index + 1}`,
    }));
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        catalogPage(firstPage, { total: 21, nextCursor: "cursor-2" }),
      )
      .mockResolvedValueOnce(
        catalogPage(
          [firstPage[0], { ...catalogScheme, scheme_id: "page-2-scheme-21" }],
          { total: 21 },
        ),
      );

    const schemes = await getAllCatalogSchemes();

    expect(schemes).toHaveLength(21);
    expect(schemes.at(-1)?.schemeId).toBe("page-2-scheme-21");
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);
  });

  it("fails rather than publishing an incomplete catalog", async () => {
    vi.mocked(fetch).mockResolvedValue(
      catalogPage([{ ...catalogScheme, scheme_id: "only-scheme" }], {
        total: 2,
      }),
    );

    await expect(getAllCatalogSchemes()).rejects.toThrow(
      "ended with 1 unique schemes; expected 2",
    );
  });

  it("omits inactive and retired schemes from sitemap routes", async () => {
    vi.mocked(fetch).mockResolvedValue(
      catalogPage([
        { ...catalogScheme, scheme_id: "listed-scheme", status: "active" },
        { ...catalogScheme, scheme_id: "unlisted-scheme", status: "inactive" },
        { ...catalogScheme, scheme_id: "gone-scheme", status: "retired" },
      ]),
    );

    const schemes = await getSchemesForSitemap();

    expect(schemes.map((scheme) => scheme.schemeId)).toEqual(["listed-scheme"]);
  });
});
