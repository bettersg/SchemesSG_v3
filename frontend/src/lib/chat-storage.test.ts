import { describe, expect, it } from "vitest";
import { makeScheme } from "@/test/fixtures/scheme";
import { deserializeChatState, serializeChatState } from "./chat-storage";

describe("chat storage", () => {
  it("round-trips the persisted chat state", () => {
    const state = {
      schemes: [makeScheme({ schemeId: "stored-scheme" })],
      messages: [{ type: "user" as const, text: "I need support" }],
      sessionId: "session-12345",
      quickReplies: [{ label: "Housing", value: "housing help" }],
    };

    expect(deserializeChatState(serializeChatState(state))).toEqual(state);
  });

  it("falls back safely when stored values are malformed", () => {
    expect(
      deserializeChatState({
        schemes: "not-json",
        messages: JSON.stringify({ type: "user", text: "not-an-array" }),
        sessionId: JSON.stringify("short"),
        quickReplies: JSON.stringify([
          { label: "Valid", value: "valid" },
          { label: "Missing value" },
        ]),
      }),
    ).toEqual({
      schemes: [],
      messages: [],
      sessionId: "",
      quickReplies: [{ label: "Valid", value: "valid" }],
    });
  });
});
