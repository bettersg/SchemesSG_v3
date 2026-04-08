import { fetchWithAuth } from "@/lib/api";
import { RawSchemeData, SearchResponse, SearchResScheme } from "../types/types";

export const mapToScheme = (rawData: RawSchemeData): SearchResScheme => ({
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
});

export const getSchemes = async (
  userQuery: string,
  nextCursor = ""
): Promise<{
  schemesRes: SearchResScheme[];
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

      const schemesRes: SearchResScheme[] = schemesData.map(mapToScheme);
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
  onChunk: (chunk: string) => void;
  onError: () => void;
  onEnd?: () => void;
};

export async function streamChat(
  query: string,
  callbacks: StreamCallbacks,
  sessionId?: string,
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
      },
    );
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();
    if (!reader) throw new Error("No reader");
    callbacks.onStart?.();

    let fullText = "";
    while (true) {
      const { done, value } = await reader.read();
      // console.log("done", done);
      if (done) {
        break;
      }
      decoder
        .decode(value)
        .split("\n\n")
        .forEach((line) => {
          // console.log(line)
          if (line.startsWith("data: ")) {
            if (fullText) {
              callbacks.onChunk(fullText);
            }
            fullText = line.slice(6);
          } else if (line) {
            fullText += line;
          }
        });
      if (fullText.startsWith('data: {"type": "done",')) {
        console.log("chunks ended");
        reader.cancel()
      }
    }
  } catch (e) {
    console.error(e)
    callbacks.onError();
  } finally {
    callbacks.onEnd?.();
  }
}

export async function searchSchemes(
  query: string,
  cursor = "",
): Promise<{ schemes: SearchResScheme[]; nextCursor: string; total: number }> {
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