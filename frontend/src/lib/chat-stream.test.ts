import { describe, expect, it } from "vitest";
import { parseSseText } from "./chat-stream";

describe("parseSseText", () => {
  it("buffers split events and emits the completion marker", () => {
    const firstChunk = 'data: {"type":"text","data":{"text":"hel';
    const firstResult = parseSseText(firstChunk);

    expect(firstResult.events).toEqual([]);

    const secondResult = parseSseText(
      `${firstResult.remainder}lo"}}\n\ndata: [DONE]\n\n`,
    );

    expect(secondResult).toEqual({
      events: [
        { type: "text", data: { text: "hello" } },
        { type: "done" },
      ],
      remainder: "",
    });
  });

  it("combines multiline data fields and ignores malformed events", () => {
    const result = parseSseText(
      [
        "data: {\"type\":\"status\",",
        "data: \"data\":{\"phase\":\"session_started\"}}",
        "",
        "data: not-json",
        "",
        "",
      ].join("\n"),
    );

    expect(result).toEqual({
      events: [
        { type: "status", data: { phase: "session_started" } },
      ],
      remainder: "",
    });
  });

  it("flushes a final event without a trailing delimiter", () => {
    expect(
      parseSseText('data: {"type":"text","data":{"text":"final"}}', {
        flush: true,
      }),
    ).toEqual({
      events: [{ type: "text", data: { text: "final" } }],
      remainder: "",
    });
  });
});
