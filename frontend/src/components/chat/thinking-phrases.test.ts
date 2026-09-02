import { describe, expect, it } from "vitest";
import { THINKING_PHRASES, thinkingPhraseOrder } from "./thinking-phrases";

describe("thinkingPhraseOrder", () => {
  it("always leads with the phrase that is true at t=0", () => {
    // Everything after the first is shuffled, but "Reading your question" is
    // the only claim guaranteed true the instant a message is sent.
    const random = () => 0.5;
    expect(thinkingPhraseOrder(random)[0]).toBe(THINKING_PHRASES[0]);
    expect(thinkingPhraseOrder(() => 0)[0]).toBe(THINKING_PHRASES[0]);
  });

  it("keeps every phrase exactly once when shuffling the tail", () => {
    const order = thinkingPhraseOrder(() => 0.999);
    expect(order).toHaveLength(THINKING_PHRASES.length);
    expect([...order].sort()).toEqual([...THINKING_PHRASES].sort());
  });

  it("shuffles the tail rather than returning source order", () => {
    const order = thinkingPhraseOrder(() => 0);
    expect(order.slice(1)).not.toEqual(THINKING_PHRASES.slice(1));
  });

  it("does not mutate the source list", () => {
    const before = [...THINKING_PHRASES];
    thinkingPhraseOrder(() => 0.25);
    expect([...THINKING_PHRASES]).toEqual(before);
  });
});
