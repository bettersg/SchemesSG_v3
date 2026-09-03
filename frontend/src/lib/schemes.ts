import { fetchWithAuth } from "@/lib/api";
import { parseSseText, type ChatStreamEvent } from "@/lib/chat-stream";
import { mapToFullScheme, mapToScheme } from "@/lib/scheme-mappers";
import { cache } from "react";
import {
  RawScheme,
  RawSchemeData,
  SearchResponse,
  Scheme,
} from "../types/types";

export type { ChatStreamEvent } from "@/lib/chat-stream";

export { mapToFullScheme, mapToScheme } from "@/lib/scheme-mappers";

export const getSchemeById = cache(
  async (schemeId: string): Promise<Scheme | null> => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) {
      throw new Error("Missing NEXT_PUBLIC_API_BASE_URL");
    }

    const response = await fetchWithAuth(`${baseUrl}/schemes/${schemeId}`, {
      // Retirements must become visible promptly so redirects/unlisted states do not remain stale.
      next: { revalidate: 300 },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const responseText = await response.text().catch(() => "");
      throw new Error(
        `Unable to fetch scheme ${schemeId} (${response.status})${
          responseText ? `: ${responseText.slice(0, 200)}` : ""
        }`,
      );
    }

    const payload = (await response.json()) as { data?: RawScheme };
    if (!payload.data) {
      return null;
    }

    return {
      ...mapToFullScheme(payload.data),
      schemeId: payload.data.scheme_id || schemeId,
    };
  },
);

// `/catalog` hides only retired schemes, while the search this replaced hid inactive
// ones too (backend NON_SEARCHABLE_STATUSES). Keep the stricter rule so the sitemap
// does not start publishing scheme pages that were deliberately unlisted.
const SITEMAP_EXCLUDED_STATUSES = new Set(["inactive", "retired"]);
const SITEMAP_PAGE_SIZE = 200;
// A pagination bug must not spin forever during a build. 50 pages covers far more
// schemes than exist; raise it before the corpus reaches SITEMAP_PAGE_SIZE * 50.
const SITEMAP_MAX_PAGES = 50;

export const getSchemesForSitemap = cache(async (): Promise<Scheme[]> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    // Secretless validation builds still publish the static sitemap routes.
    return [];
  }

  const schemes: Scheme[] = [];
  const seen = new Set<string>();
  let cursor = "";

  // The catalog enumerates the corpus directly, so page it rather than
  // approximating "everything" with one broad search query, which could only ever
  // return schemes that have an embedding.
  for (let page = 0; page < SITEMAP_MAX_PAGES; page += 1) {
    const url = new URL(`${baseUrl}/catalog`);
    url.searchParams.set("limit", String(SITEMAP_PAGE_SIZE));
    if (cursor) {
      url.searchParams.set("cursor", cursor);
    }

    // Keep the pages already collected; a partial sitemap beats no sitemap, and a
    // build-time network failure must not take the static routes down with it.
    let payload: SearchResponse;
    try {
      const response = await fetchWithAuth(url.toString(), {
        next: { revalidate: 86_400 },
      });
      if (!response.ok) {
        break;
      }
      payload = (await response.json()) as SearchResponse;
    } catch (error) {
      console.error("Sitemap catalog page failed", error);
      break;
    }

    const rawSchemes = payload.data
      ? Array.isArray(payload.data)
        ? payload.data
        : [payload.data]
      : [];

    for (const raw of rawSchemes) {
      const scheme = mapToFullScheme(raw as RawScheme);
      if (scheme.status && SITEMAP_EXCLUDED_STATUSES.has(scheme.status)) {
        continue;
      }
      if (!scheme.schemeId || seen.has(scheme.schemeId)) {
        continue;
      }
      seen.add(scheme.schemeId);
      schemes.push(scheme);
    }

    if (!payload.has_more || !payload.next_cursor) {
      break;
    }
    cursor = payload.next_cursor;

    // Hitting the cap means the sitemap is silently short. Say so in the build log.
    if (page === SITEMAP_MAX_PAGES - 1) {
      console.warn(
        `Sitemap stopped at the ${SITEMAP_MAX_PAGES}-page cap with more schemes available; raise SITEMAP_MAX_PAGES.`,
      );
    }
  }

  return schemes;
});

type StreamCallbacks = {
  onStart?: () => void;
  onEvent: (event: ChatStreamEvent) => void;
  onError: (error: unknown) => void;
  onEnd?: () => void;
};

export async function streamChat(
  query: string,
  callbacks: StreamCallbacks,
  sessionId?: string,
  signal?: AbortSignal,
) {
  try {
    const body: { message: string; sessionID?: string } = { message: query };
    if (sessionId) {
      body.sessionID = sessionId;
    }
    const res = await fetchWithAuth(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/agent_chat_message`,
      {
        method: "POST",
        body: JSON.stringify(body),
        signal,
      },
    );
    // throw new Error("test");
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) throw new Error("No reader");
    callbacks.onStart?.();

    let buffer = "";

    const processEvents = (text: string, flush = false) => {
      const parsed = parseSseText(text, { flush });
      buffer = parsed.remainder;

      for (const event of parsed.events) {
        callbacks.onEvent(event);
        if (event.type === "done") return true;
      }

      return false;
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      if (processEvents(buffer)) {
        await reader.cancel();
        return;
      }
    }

    buffer += decoder.decode();
    processEvents(buffer, true);
  } catch (e) {
    if ((e as DOMException)?.name === "AbortError") return;
    console.error(e);
    callbacks.onError(e);
  } finally {
    callbacks.onEnd?.();
  }
}

export async function getSchemesCategory(
  category = "",
  cursor = "",
): Promise<{ schemes: Scheme[]; nextCursor: string; total: number }> {
  const url = new URL(`${process.env.NEXT_PUBLIC_API_BASE_URL}/catalog`);
  const normalizedCategory = category.replace(/\+/g, " ").trim();

  url.searchParams.set("limit", "20");
  if (normalizedCategory) {
    url.searchParams.set("category", normalizedCategory);
  }
  if (cursor) {
    url.searchParams.set("cursor", cursor);
  }

  try {
    const res = await fetchWithAuth(url.toString(), {
      method: "GET",
    });

    if (res.status === 404) {
      return { schemes: [], nextCursor: "", total: 0 };
    }
    if (!res.ok) {
      throw new Error(`Catalog fetch failed: ${res.status}`);
    }

    const data = (await res.json()) as SearchResponse;
    const raw = data.data
      ? Array.isArray(data.data)
        ? data.data
        : [data.data]
      : [];

    return {
      schemes: raw.map((r: RawSchemeData) => mapToScheme(r)),
      nextCursor: data.has_more && data.next_cursor ? data.next_cursor : "",
      total: data.total_count ?? 0,
    };
  } catch {
    return { schemes: [], nextCursor: "", total: 0 };
  }
}
