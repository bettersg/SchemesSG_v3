import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const getAuthToken = vi.hoisted(() => vi.fn());

vi.mock("@/lib/auth-gateway", () => ({ getAuthToken }));

import { fetchWithAuth } from "./api";

describe("authenticated fetch", () => {
  beforeEach(() => {
    getAuthToken.mockResolvedValue("firebase-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response()));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("adds authorization while preserving caller Headers", async () => {
    await fetchWithAuth("https://api.test/protected", {
      method: "POST",
      headers: new Headers({
        "Content-Type": "application/x-ndjson",
        "X-Request-ID": "request-123",
      }),
    });

    const [, init] = vi.mocked(fetch).mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(headers.get("Authorization")).toBe("Bearer firebase-token");
    expect(headers.get("Content-Type")).toBe("application/x-ndjson");
    expect(headers.get("X-Request-ID")).toBe("request-123");
  });
});
