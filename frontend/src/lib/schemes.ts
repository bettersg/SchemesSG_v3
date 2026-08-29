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

export const getSchemesForSitemap = cache(async (): Promise<Scheme[]> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    throw new Error("Missing NEXT_PUBLIC_API_BASE_URL");
  }

  const response = await fetchWithAuth(`${baseUrl}/schemes_search`, {
    method: "POST",
    body: JSON.stringify({
      query:
        "financial assistance healthcare housing employment education family eldercare disability mental health food support social assistance",
      limit: 1000,
      top_k: 1000,
      similarity_threshold: 0,
      cursor: null,
    }),
    next: { revalidate: 86_400 },
  });

  if (!response.ok) {
    return [];
  }

  const payload = (await response.json()) as SearchResponse;
  const rawSchemes = payload.data
    ? Array.isArray(payload.data)
      ? payload.data
      : [payload.data]
    : [];

  const seen = new Set<string>();
  return rawSchemes
    .map((raw) => mapToFullScheme(raw as RawScheme))
    .filter((scheme) => {
      if (!scheme.schemeId || seen.has(scheme.schemeId)) {
        return false;
      }
      seen.add(scheme.schemeId);
      return true;
    });
});

export const getSchemes = async (
  userQuery: string,
  nextCursor = "",
): Promise<{
  schemesRes: Scheme[];
  sessionId: string;
  totalCount: number;
  nextCursor: string;
}> => {
  const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;

  const requestBody = {
    query: userQuery,
    limit: 20,
    top_k: 50,
    similarity_threshold: 0,
    cursor: nextCursor || null, // Send null instead of empty string
  };

  try {
    const response = await fetchWithAuth(url, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const res = (await response.json()) as SearchResponse;
    console.log("Search response:", res); // Debug

    const sessionId: string = res.sessionID || "";
    const totalCount: number = res.total_count || 0;
    const hasMore: boolean = res.has_more || false;
    const nextCursor: string =
      res.next_cursor && hasMore ? res.next_cursor : "";

    // Check if data exists in the response
    if (res.data) {
      let schemesData;
      // Handle both array and single object responses
      if (Array.isArray(res.data)) {
        schemesData = res.data;
      } else {
        // If it's a single object, convert to array
        schemesData = [res.data];
      }

      const schemesRes: Scheme[] = schemesData.map(mapToScheme);
      console.log("Mapped schemes:", schemesRes); // Debug
      return { schemesRes, sessionId, totalCount, nextCursor };
    } else {
      console.error("Unexpected response format:", res);
      return { schemesRes: [], sessionId, totalCount, nextCursor };
    }
  } catch (error) {
    console.error("Error making POST request:", error);
    return { schemesRes: [], sessionId: "", totalCount: 0, nextCursor: "" };
  }
};

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

export async function searchSchemes(
  query: string,
  cursor = "",
): Promise<{ schemes: Scheme[]; nextCursor: string; total: number }> {
  const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;
  try {
    const res = await fetchWithAuth(url, {
      method: "POST",
      body: JSON.stringify({
        query: query || "social assistance",
        limit: 20,
        top_k: 50,
        similarity_threshold: 0,
        cursor: cursor || null,
      }),
    });
    if (!res.ok) throw new Error("fetch failed");
    const data = (await res.json()) as SearchResponse;
    console.log(data);
    const raw = data.data
      ? Array.isArray(data.data)
        ? data.data
        : [data.data]
      : [];
    return {
      schemes: raw.map((r: RawSchemeData) => mapToScheme(r)),
      nextCursor: data.has_more && data.next_cursor ? data.next_cursor : "",
      total: data.total_count || 0,
    };
  } catch {
    return { schemes: [], nextCursor: "", total: 0 };
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
