import { fetchWithAuth } from "@/lib/api";
import { RawSchemeData, SearchResponse, Scheme } from "../types/types";

export const mapToScheme = (rawData: RawSchemeData): Scheme => ({
  schemeType: rawData["scheme_type"] || rawData["Scheme Type"] || [],
  schemeName: rawData["scheme"] || rawData["Scheme"] || "",
  targetAudience: rawData["who_is_it_for"] || rawData["Who's it for"] || [],
  agency: rawData["agency"] || rawData["Agency"] || "",
  description: rawData["description"] || rawData["Description"] || "",
  scrapedText: rawData["scraped_text"] || "",
  benefits: rawData["what_it_gives"] || rawData["What it gives"] || [],
  link: rawData["link"] || rawData["Link"] || "",
  image: rawData["image"] || rawData["Image"] || "",
  searchBooster:
    rawData["search_booster"] || rawData["search_booster(WL)"] || "",
  schemeId: rawData["scheme_id"] || "",
  query: rawData["query"] || "",
  similarity: rawData["Similarity"] || 0,
  quintile: rawData["Quintile"] || 0,
  planningArea: rawData["planning_area"] || "",
  summary: rawData["summary"] || "",
  contact: [],
  howToApply:
    (rawData as Record<string, string | undefined>)["how_to_apply"] ||
    (rawData as Record<string, string | undefined>)["How to apply"] ||
    "",
  eligibilityText:
    (rawData as Record<string, string | undefined>)["eligibility_text"] ||
    (rawData as Record<string, string | undefined>)["Eligibility"] ||
    "",
  lastUpdated:
    (rawData as Record<string, string | undefined>)["last_updated"] ||
    (rawData as Record<string, string | undefined>)["Last updated"] ||
    "",
  serviceArea:
    (rawData as Record<string, string | undefined>)["service_area"] ||
    (rawData as Record<string, string | undefined>)["Service area"] ||
    "",
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

export type ChatStreamEvent =
  | {
      type: "chunk";
      data: {
        chunk?: string;
        content?: string;
        text?: string;
        blockIndex?: number;
        block_index?: number;
        messageIndex?: number;
        message_index?: number;
      };
    }
  | {
      type: "status";
      data: {
        label?: string;
        phase?: string;
        sessionID?: string;
        sessionId?: string;
      };
    }
  | {
      type: "schemes_update";
      data: {
        schemes?: RawSchemeData[];
      };
    }
  | {
      type: "followups";
      data: {
        items?: Record<string, string>;
      };
    }
  | {
      type: "done";
      data?: Record<string, unknown>;
    }
  | {
      type: string;
      data?: Record<string, unknown>;
    };

function parseStreamEvent(raw: string): ChatStreamEvent | null {
  const payload = raw.trim();
  if (!payload || payload === "[DONE]") {
    return { type: "done" };
  }

  try {
    return JSON.parse(payload) as ChatStreamEvent;
  } catch (error) {
    console.warn("Failed to parse chat stream event", { payload, error });
    return null;
  }
}

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

    const processEvent = (eventText: string) => {
      const dataLines = eventText
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data: "))
        .map((line) => line.slice(6));

      if (dataLines.length === 0) return false;

      const event = parseStreamEvent(dataLines.join("\n"));
      if (!event) return false;

      callbacks.onEvent(event);
      return event.type === "done";
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() ?? "";

      for (const eventText of events) {
        if (processEvent(eventText)) {
          await reader.cancel();
          return;
        }
      }
    }

    buffer += decoder.decode();
    if (buffer.trim()) {
      processEvent(buffer);
    }
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
