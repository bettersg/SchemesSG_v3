import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { catalogScheme } from "@/test/fixtures/catalog";
import type { RawScheme, RawSchemeData } from "@/types/types";

vi.mock("server-only", () => ({}));

import { getSchemesForSitemap } from "./schemes.server";
import { hasIndexableContent } from "./scheme-indexing";

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

const fullSchemeResponse = (overrides: Partial<RawScheme> = {}) =>
  Response.json({
    data: {
      ...catalogScheme,
      eligibility: "",
      how_to_apply: "",
      ...overrides,
    } as RawScheme,
  });

beforeEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
  vi.stubGlobal("fetch", vi.fn());
});

afterEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = configuredApiUrl;
  vi.unstubAllGlobals();
});

describe("sitemap enrichment for indexability", () => {
  it("includes a scheme with description without fetching full details", async () => {
    const withDescription = {
      ...catalogScheme,
      scheme_id: "has-description",
      description: "Full description text",
    };

    vi.mocked(fetch).mockResolvedValueOnce(
      catalogPage([withDescription], { total: 1 }),
    );

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(1);
    expect(schemes[0].schemeId).toBe("has-description");
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1);
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain("/catalog");
  });

  it("includes eligibility-only scheme by fetching full details", async () => {
    const noDescription = {
      ...catalogScheme,
      scheme_id: "eligibility-only",
      description: "",
      llm_description: "",
    };

    vi.mocked(fetch)
      .mockResolvedValueOnce(catalogPage([noDescription], { total: 1 }))
      .mockResolvedValueOnce(
        fullSchemeResponse({
          scheme_id: "eligibility-only",
          eligibility: "Must be a resident",
          how_to_apply: "",
          description: "",
        }),
      );

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(1);
    expect(schemes[0].schemeId).toBe("eligibility-only");
    expect(schemes[0].eligibilityText).toBe("Must be a resident");
    expect(hasIndexableContent(schemes[0])).toBe(true);
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);
    expect(String(vi.mocked(fetch).mock.calls[1][0])).toContain(
      "/schemes/eligibility-only",
    );
  });

  it("includes application-only scheme by fetching full details", async () => {
    const noDescription = {
      ...catalogScheme,
      scheme_id: "application-only",
      description: "",
      llm_description: "",
    };

    vi.mocked(fetch)
      .mockResolvedValueOnce(catalogPage([noDescription], { total: 1 }))
      .mockResolvedValueOnce(
        fullSchemeResponse({
          scheme_id: "application-only",
          eligibility: "",
          how_to_apply: "Apply online at agency website",
          description: "",
        }),
      );

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(1);
    expect(schemes[0].schemeId).toBe("application-only");
    expect(schemes[0].howToApply).toBe("Apply online at agency website");
    expect(hasIndexableContent(schemes[0])).toBe(true);
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);
  });

  it("excludes scheme with no indexable content even after full fetch", async () => {
    const noDescription = {
      ...catalogScheme,
      scheme_id: "no-content",
      description: "",
      llm_description: "",
    };

    vi.mocked(fetch)
      .mockResolvedValueOnce(catalogPage([noDescription], { total: 1 }))
      .mockResolvedValueOnce(
        fullSchemeResponse({
          scheme_id: "no-content",
          eligibility: "",
          how_to_apply: "",
          description: "",
        }),
      );

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(0);
  });

  it("excludes scheme when full fetch fails", async () => {
    const noDescription = {
      ...catalogScheme,
      scheme_id: "fetch-fails",
      description: "",
      llm_description: "",
    };

    vi.mocked(fetch)
      .mockResolvedValueOnce(catalogPage([noDescription], { total: 1 }))
      .mockRejectedValueOnce(new Error("Network error"));

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(0);
  });

  it("processes mixed schemes correctly", async () => {
    const withDesc = {
      ...catalogScheme,
      scheme_id: "with-desc",
      description: "Has description",
    };
    const needsEnrich = {
      ...catalogScheme,
      scheme_id: "needs-enrich",
      description: "",
      llm_description: "",
    };

    vi.mocked(fetch)
      .mockResolvedValueOnce(catalogPage([withDesc, needsEnrich], { total: 2 }))
      .mockResolvedValueOnce(
        fullSchemeResponse({
          scheme_id: "needs-enrich",
          eligibility: "Residents only",
        }),
      );

    const schemes = await getSchemesForSitemap();

    expect(schemes).toHaveLength(2);
    expect(schemes.map((s) => s.schemeId)).toEqual(
      expect.arrayContaining(["with-desc", "needs-enrich"]),
    );
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(2);
  });
});
