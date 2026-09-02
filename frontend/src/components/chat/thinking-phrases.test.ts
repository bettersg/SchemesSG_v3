import { describe, expect, it } from "vitest";
import { THINKING_PHRASES, thinkingPhraseOrder } from "./thinking-phrases";

describe("thinkingPhraseOrder", () => {
  const CLOSER = THINKING_PHRASES[THINKING_PHRASES.length - 1];

  it("varies the opener rather than pinning one phrase", () => {
    // The regression this guards: a pinned opener meant every send showed the
    // same words, because a healthy backend replaces the list before the
    // rotation's dwell floor elapses, so no second phrase is ever seen.
    const openers = new Set(
      Array.from({ length: 40 }, () => thinkingPhraseOrder()[0]),
    );
    expect(openers.size).toBeGreaterThan(1);
  });

  it("holds the wait-tolerant closer at the end", () => {
    // "Still with you" is a lie two seconds in, so no shuffle may move it
    // forward regardless of what the RNG returns.
    for (const random of [() => 0, () => 0.5, () => 0.999, Math.random]) {
      expect(thinkingPhraseOrder(random).at(-1)).toBe(CLOSER);
    }
  });

  it("keeps every phrase exactly once when shuffling", () => {
    const order = thinkingPhraseOrder(() => 0.999);
    expect(order).toHaveLength(THINKING_PHRASES.length);
    expect([...order].sort()).toEqual([...THINKING_PHRASES].sort());
  });

  it("shuffles rather than returning source order", () => {
    const order = thinkingPhraseOrder(() => 0);
    expect(order).not.toEqual([...THINKING_PHRASES]);
  });

  it("does not mutate the source list", () => {
    const before = [...THINKING_PHRASES];
    thinkingPhraseOrder(() => 0.25);
    expect([...THINKING_PHRASES]).toEqual(before);
  });
});
