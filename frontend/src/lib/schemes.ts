import { fetchWithAuth } from "@/lib/api";
import { parseSseText, type ChatStreamEvent } from "@/lib/chat-stream";
import { mapCatalogScheme } from "@/lib/scheme-mappers";
import { RawSchemeData, SearchResponse, Scheme } from "../types/types";

export type { ChatStreamEvent } from "@/lib/chat-stream";

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
    const res = await fetch(url, {
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
      schemes: raw.map((r: RawSchemeData) => mapCatalogScheme(r)),
      nextCursor: data.has_more && data.next_cursor ? data.next_cursor : "",
      total: data.total_count ?? 0,
    };
  } catch {
    return { schemes: [], nextCursor: "", total: 0 };
  }
}
