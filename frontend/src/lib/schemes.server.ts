import "server-only";

import { cache } from "react";
import type { CatalogCategory } from "./design-system/categories";
import type { RawScheme, Scheme } from "../types/types";
import { serverFetchWithAuth } from "./firebase-auth.server";
import { mapToFullScheme } from "./scheme-mappers";

export type CatalogPageData = {
  schemes: Scheme[];
  total: number;
  nextCursor: string;
};

type CatalogResponse = {
  data?: RawScheme[] | RawScheme;
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
  url.searchParams.set("limit", "20");
  if (category && category !== "All") {
    url.searchParams.set("category", category);
  }
  if (cursor) url.searchParams.set("cursor", cursor);

  const response = await serverFetchWithAuth(url, {
    method: "GET",
    next: { revalidate: 86_400 },
  });
  if (response.status === 404) {
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
    payload.total_count !== undefined &&
    (!Number.isFinite(payload.total_count) || payload.total_count < 0)
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
    schemes: rawSchemes.map(mapToFullScheme),
    total: payload.total_count ?? rawSchemes.length,
    nextCursor:
      payload.has_more === true && payload.next_cursor
        ? payload.next_cursor
        : "",
  };
}

const MAX_CATALOG_PAGES = 10_000;

async function getAllCatalogSchemesUncached(): Promise<Scheme[]> {
  const schemes: Scheme[] = [];
  const seenIds = new Set<string>();
  const seenCursors = new Set<string>();
  let cursor = "";

  for (let page = 0; page < MAX_CATALOG_PAGES; page += 1) {
    const result = await getCatalogData(undefined, cursor);
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
      return schemes;
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
    const response = await serverFetchWithAuth(
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
