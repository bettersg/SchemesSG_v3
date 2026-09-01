import { HttpResponse } from "msw";

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
