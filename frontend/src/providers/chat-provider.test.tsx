import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { ChatProvider, useChat } from "./chat-provider";
import { CHAT_STORAGE_KEYS } from "@/lib/chat-storage";
import type { Message } from "@/types/chat";

/**
 * `consumeIsResumedTurn` decides whether a send is reported to analytics as a
 * real submit or as the automatic re-fire of an unanswered turn after a
 * refresh. Both failure directions corrupt the send count, and neither is
 * visible in the UI, so they can only be caught here.
 */

const seedStoredChat = (messages: Message[]) => {
  sessionStorage.setItem(CHAT_STORAGE_KEYS.messages, JSON.stringify(messages));
  sessionStorage.setItem(
    CHAT_STORAGE_KEYS.sessionId,
    JSON.stringify("session-12345"),
  );
};

const wrapper = ({ children }: { children: ReactNode }) => (
  <ChatProvider>{children}</ChatProvider>
);

const renderChat = () => renderHook(() => useChat(), { wrapper });

afterEach(() => {
  sessionStorage.clear();
});

describe("ChatProvider resumed-turn accounting", () => {
  it("reports a restored unanswered turn as a resume exactly once", () => {
    seedStoredChat([{ type: "user", text: "help with rent" }]);

    const { result } = renderChat();
    const turnKey = "1:help with rent";

    expect(result.current.consumeIsResumedTurn(turnKey)).toBe(true);
    // Clears on match. If it latched, the same question asked again later in
    // the session would be mislabelled a resume and undercount real sends.
    expect(result.current.consumeIsResumedTurn(turnKey)).toBe(false);
  });

  it("reports a send in a fresh session as a real submit", () => {
    const { result } = renderChat();

    expect(result.current.consumeIsResumedTurn("1:help with rent")).toBe(false);
    expect(result.current.hasActiveChat).toBe(false);
  });

  it("reports nothing as a resume when the restored turn was already answered", () => {
    seedStoredChat([
      { type: "user", text: "help with rent" },
      { type: "bot", text: "Here are some schemes" },
    ]);

    const { result } = renderChat();

    // No turn is awaiting a reply, so there is nothing for the page to re-fire.
    expect(result.current.consumeIsResumedTurn("2:help with rent")).toBe(false);
    expect(result.current.consumeIsResumedTurn("1:help with rent")).toBe(false);
    expect(result.current.hasActiveChat).toBe(true);
  });

  it("does not treat a different question as the restored turn", () => {
    seedStoredChat([{ type: "user", text: "help with rent" }]);

    const { result } = renderChat();

    expect(result.current.consumeIsResumedTurn("1:help with childcare")).toBe(
      false,
    );
    // The real resume still works afterwards: a miss must not clear the key.
    expect(result.current.consumeIsResumedTurn("1:help with rent")).toBe(true);
  });
});
