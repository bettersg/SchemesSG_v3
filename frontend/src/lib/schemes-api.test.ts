import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { catalogScheme } from "@/test/fixtures/catalog";

const fetchWithAuth = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api", () => ({ fetchWithAuth }));

import {
  getSchemeById,
  getSchemes,
  getSchemesCategory,
  searchSchemes,
  streamChat,
} from "./schemes";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

beforeEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.test";
  fetchWithAuth.mockReset();
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

afterEach(() => {
  process.env.NEXT_PUBLIC_API_BASE_URL = configuredApiUrl;
  vi.restoreAllMocks();
});

describe("scheme API", () => {
  it("returns a mapped scheme detail from the public detail endpoint", async () => {
    fetchWithAuth.mockResolvedValue(
      Response.json({
        data: {
          scheme_id: "detail-scheme",
          scheme: "Detail Scheme",
          agency: "Support Agency",
          scheme_type: ["Financial Assistance"],
        },
      }),
    );

    await expect(getSchemeById("detail-scheme")).resolves.toMatchObject({
      schemeId: "detail-scheme",
      schemeName: "Detail Scheme",
      agency: "Support Agency",
      schemeType: ["Financial Assistance"],
    });
    expect(fetchWithAuth).toHaveBeenCalledWith(
      "https://api.test/schemes/detail-scheme",
      { next: { revalidate: 300 } },
    );
  });

  it("returns null when a scheme detail is absent", async () => {
    fetchWithAuth.mockResolvedValue(new Response(null, { status: 404 }));

    await expect(getSchemeById("missing-scheme")).resolves.toBeNull();
  });

  it("surfaces an actionable scheme-detail API error", async () => {
    fetchWithAuth.mockResolvedValue(
      new Response("upstream unavailable", { status: 503 }),
    );

    await expect(getSchemeById("failed-scheme")).rejects.toThrow(
      "Unable to fetch scheme failed-scheme (503): upstream unavailable",
    );
  });

  it("maps paginated search results and sends the cursor contract", async () => {
    fetchWithAuth.mockResolvedValue(
      Response.json({
        data: catalogScheme,
        sessionID: "session-123",
        total_count: 7,
        has_more: true,
        next_cursor: "cursor-2",
      }),
    );

    await expect(getSchemes("housing support", "cursor-1")).resolves.toEqual({
      schemesRes: [
        expect.objectContaining({ schemeId: "test-support-scheme" }),
      ],
      sessionId: "session-123",
      totalCount: 7,
      nextCursor: "cursor-2",
    });
    expect(JSON.parse(fetchWithAuth.mock.calls[0][1].body)).toMatchObject({
      query: "housing support",
      cursor: "cursor-1",
      limit: 20,
    });
  });

  it("uses the default query and maps a search result list", async () => {
    fetchWithAuth.mockResolvedValue(
      Response.json({ data: [catalogScheme], total_count: 1 }),
    );

    await expect(searchSchemes("")).resolves.toEqual({
      schemes: [expect.objectContaining({ schemeName: "Test Support Scheme" })],
      nextCursor: "",
      total: 1,
    });
    expect(JSON.parse(fetchWithAuth.mock.calls[0][1].body).query).toBe(
      "social assistance",
    );
  });

  it("normalizes category and cursor parameters for catalog loading", async () => {
    fetchWithAuth.mockResolvedValue(
      Response.json({
        data: [catalogScheme],
        total_count: 1,
        has_more: true,
        next_cursor: "catalog-cursor-2",
      }),
    );

    await expect(
      getSchemesCategory("Financial+Assistance", "catalog-cursor-1"),
    ).resolves.toEqual({
      schemes: [expect.objectContaining({ schemeId: "test-support-scheme" })],
      nextCursor: "catalog-cursor-2",
      total: 1,
    });
    expect(fetchWithAuth.mock.calls[0][0]).toBe(
      "https://api.test/catalog?limit=20&category=Financial+Assistance&cursor=catalog-cursor-1",
    );
  });

  it("returns stable empty states when search and catalog requests fail", async () => {
    fetchWithAuth
      .mockRejectedValueOnce(new Error("search unavailable"))
      .mockResolvedValueOnce(new Response(null, { status: 404 }));

    const searchResult = await searchSchemes("support");
    const catalogResult = await getSchemesCategory("Support");

    expect({ searchResult, catalogResult }).toEqual({
      searchResult: { schemes: [], nextCursor: "", total: 0 },
      catalogResult: { schemes: [], nextCursor: "", total: 0 },
    });
  });
});

describe("chat streaming", () => {
  it("delivers streamed events in order and closes after the done marker", async () => {
    const encoder = new TextEncoder();
    let streamCancelled = false;
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode('data: {"type":"text","data":{"text":"hello"}}\n\n'),
        );
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      },
      cancel() {
        streamCancelled = true;
      },
    });
    fetchWithAuth.mockResolvedValue(new Response(body));
    const lifecycle: string[] = [];

    await streamChat(
      "help me",
      {
        onStart: () => lifecycle.push("start"),
        onEvent: (event) => lifecycle.push(event.type),
        onError: () => lifecycle.push("error"),
        onEnd: () => lifecycle.push("end"),
      },
      "session-123",
    );

    expect(lifecycle).toEqual(["start", "text", "done", "end"]);
    expect(streamCancelled).toBe(true);
    expect(JSON.parse(fetchWithAuth.mock.calls[0][1].body)).toEqual({
      message: "help me",
      sessionID: "session-123",
    });
  });

  it("treats cancellation as recovery instead of a stream error", async () => {
    fetchWithAuth.mockRejectedValue(
      new DOMException("The operation was aborted", "AbortError"),
    );
    const onError = vi.fn();
    const onEnd = vi.fn();

    await streamChat("cancel me", { onEvent: vi.fn(), onError, onEnd });

    expect(onError).not.toHaveBeenCalled();
    expect(onEnd).toHaveBeenCalledOnce();
  });
});
