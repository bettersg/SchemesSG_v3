import "server-only";

import { cache } from "react";
import type { CatalogCategory } from "./design-system/categories";
import type {
  CatalogPageData,
  RawScheme,
  RawSchemeData,
  Scheme,
} from "../types/types";
import { mapCatalogScheme, mapToFullScheme } from "./scheme-mappers";

type CatalogResponse = {
  data?: RawSchemeData[] | RawSchemeData;
  total_count?: number;
  next_cursor?: string;
  has_more?: boolean;
};

const getApiBaseUrl = () => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) throw new Error("Missing NEXT_PUBLIC_API_BASE_URL");
  return baseUrl;
};

export async function getCatalogData(
  category?: CatalogCategory,
  cursor = "",
): Promise<CatalogPageData> {
  const url = new URL(`${getApiBaseUrl()}/catalog`);
  url.searchParams.set("limit", String(CATALOG_PAGE_SIZE));
  if (category && category !== "All") {
    url.searchParams.set("category", category);
  }
  if (cursor) url.searchParams.set("cursor", cursor);

  const response = await fetch(url, {
    method: "GET",
    next: { revalidate: 86_400 },
  });
  if (response.status === 404) {
    if (cursor) {
      throw new Error("Catalog continuation returned 404");
    }
    return { schemes: [], total: 0, nextCursor: "" };
  }
  if (!response.ok) {
    throw new Error(`Catalog fetch failed with status ${response.status}`);
  }

  const payload = (await response.json()) as CatalogResponse;
  if (!payload || typeof payload !== "object" || payload.data === undefined) {
    throw new Error("Catalog response is missing data");
  }
  const rawSchemes = Array.isArray(payload.data)
    ? payload.data
    : [payload.data];
  if (
    !Number.isInteger(payload.total_count) ||
    (payload.total_count as number) < 0
  ) {
    throw new Error("Catalog response has invalid total_count");
  }
  if (
    payload.has_more === true &&
    (typeof payload.next_cursor !== "string" || !payload.next_cursor)
  ) {
    throw new Error("Catalog response has_more without next_cursor");
  }

  return {
    schemes: rawSchemes.map(mapCatalogScheme),
    total: payload.total_count as number,
    nextCursor:
      payload.has_more === true && payload.next_cursor
        ? payload.next_cursor
        : "",
  };
}

const CATALOG_PAGE_SIZE = 20;
const MAX_CATALOG_PAGES = 500;

/**
 * Fetch every catalog page so Next.js can generate all scheme detail routes.
 *
 * The enumeration validates that:
 * - the reported total remains unchanged across pages;
 * - the total fits within the hard page-count safety cap;
 * - every row has a scheme ID and duplicate IDs are ignored;
 * - continuation pages add at least one new scheme;
 * - cursors do not repeat;
 * - pagination does not continue beyond the expected number of pages; and
 * - the final number of unique schemes matches the reported total.
 *
 * Any inconsistent or non-progressing response fails the build instead of
 * silently generating an incomplete set of scheme pages.
 */
async function getAllCatalogSchemesUncached(): Promise<Scheme[]> {
  const schemes: Scheme[] = [];
  const seenIds = new Set<string>();
  const seenCursors = new Set<string>();
  let cursor = "";
  let expectedTotal: number | null = null;
  let expectedPages: number | null = null;

  for (let page = 0; page < MAX_CATALOG_PAGES; page += 1) {
    const result = await getCatalogData(undefined, cursor);
    if (expectedTotal === null) {
      expectedTotal = result.total;
      expectedPages = Math.ceil(expectedTotal / CATALOG_PAGE_SIZE);
      if (expectedPages > MAX_CATALOG_PAGES) {
        throw new Error(
          `Catalog enumeration requires ${expectedPages} pages, above the ${MAX_CATALOG_PAGES}-page safety cap`,
        );
      }
    } else if (result.total !== expectedTotal) {
      throw new Error(
        `Catalog total changed during enumeration (${expectedTotal} to ${result.total})`,
      );
    }

    let added = 0;
    for (const scheme of result.schemes) {
      if (!scheme.schemeId) throw new Error("Catalog row is missing scheme id");
      if (!seenIds.has(scheme.schemeId)) {
        seenIds.add(scheme.schemeId);
        schemes.push(scheme);
        added += 1;
      }
    }
    if (!result.nextCursor) {
      if (schemes.length === 0) {
        throw new Error("Catalog enumeration returned no schemes");
      }
      if (schemes.length !== expectedTotal) {
        throw new Error(
          `Catalog enumeration ended with ${schemes.length} unique schemes; expected ${expectedTotal}`,
        );
      }
      return schemes;
    }
    if (schemes.length >= expectedTotal) {
      throw new Error("Catalog returned a cursor after reaching total_count");
    }
    if (expectedPages !== null && page + 1 >= expectedPages) {
      throw new Error(
        `Catalog pagination continued beyond ${expectedPages} expected pages`,
      );
    }
    if (seenCursors.has(result.nextCursor)) {
      throw new Error(`Repeated catalog cursor: ${result.nextCursor}`);
    }
    if (added === 0) {
      throw new Error("Catalog continuation page made no progress");
    }
    seenCursors.add(result.nextCursor);
    cursor = result.nextCursor;
  }
  throw new Error(`Catalog enumeration exceeded ${MAX_CATALOG_PAGES} pages`);
}

export const getAllCatalogSchemes = cache(getAllCatalogSchemesUncached);

export const getSchemeById = cache(
  async (schemeId: string): Promise<Scheme | null> => {
    const response = await fetch(
      `${getApiBaseUrl()}/schemes/${encodeURIComponent(schemeId)}`,
      { next: { revalidate: 86_400 } },
    );
    if (response.status === 404) return null;
    if (!response.ok) {
      throw new Error(
        `Unable to fetch scheme ${schemeId} (${response.status})`,
      );
    }
    const payload = (await response.json()) as { data?: RawScheme };
    if (!payload.data) return null;
    return {
      ...mapToFullScheme(payload.data),
      schemeId: payload.data.scheme_id || schemeId,
    };
  },
);
