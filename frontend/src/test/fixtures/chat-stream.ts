import { HttpResponse } from "msw";
import { vi } from "vitest";

/** Server-sent-event body the chat endpoint returns, terminated with [DONE]. */
export function streamResponse(events: unknown[]) {
  const body = [
    ...events.map((event) => `data: ${JSON.stringify(event)}\n\n`),
    "data: [DONE]\n\n",
  ].join("");
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
    },
  });

  return new HttpResponse(stream, {
    headers: { "Content-Type": "text/event-stream" },
  });
}

/**
 * jsdom lacks matchMedia, which the composer's hover query needs, and the chat
 * error paths log through console.error on purpose.
 */
export function stubChatEnvironment() {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn((query: string) => ({
      matches: query.includes("any-hover: hover"),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  });
}
