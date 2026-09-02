import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WordRotate } from "./word-rotate";

// Asserted through the scheduled dwells rather than the swapped text:
// AnimatePresence mode="wait" holds the next word back until the previous one
// finishes exiting, and jsdom never completes that exit, so a DOM assertion here
// would be testing framer-motion. The visible swap is covered in the browser by
// e2e/chat-thinking-indicator.spec.ts.
let setTimeoutSpy: ReturnType<typeof vi.spyOn>;

/** Dwell delays this component asked for, filtered clear of framer/React noise. */
const scheduledDwells = (): number[] =>
  setTimeoutSpy.mock.calls
    .map((call: unknown[]) => Number(call[1] ?? 0))
    .filter((delay: number) => delay >= 500);

beforeEach(() => {
  vi.useFakeTimers();
  setTimeoutSpy = vi.spyOn(window, "setTimeout");
});

afterEach(() => {
  vi.useRealTimers();
});

describe("WordRotate", () => {
  it("dwells for minDuration when the roll is lowest", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    render(
      <WordRotate
        words={["first", "second"]}
        minDuration={1800}
        maxDuration={3200}
      />,
    );

    expect(scheduledDwells()).toEqual([1800]);
  });

  it("dwells for maxDuration when the roll is highest", () => {
    vi.spyOn(Math, "random").mockReturnValue(1);
    render(
      <WordRotate
        words={["first", "second"]}
        minDuration={1800}
        maxDuration={3200}
      />,
    );

    expect(scheduledDwells()).toEqual([3200]);
  });

  it("re-rolls a fresh dwell for each step instead of reusing one interval", () => {
    vi.spyOn(Math, "random")
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(1)
      .mockReturnValue(0.5);
    render(
      <WordRotate words={["a", "b", "c"]} minDuration={1000} maxDuration={2000} />,
    );

    expect(scheduledDwells()).toEqual([1000]);
    act(() => vi.advanceTimersByTime(1000));
    // A setInterval would have kept ticking at 1000ms; this asked for its own.
    expect(scheduledDwells()).toEqual([1000, 2000]);
    act(() => vi.advanceTimersByTime(2000));
    expect(scheduledDwells()).toEqual([1000, 2000, 1500]);
  });

  it("keeps a fixed cadence when both bounds are equal", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.7);
    render(<WordRotate words={["a", "b"]} minDuration={2500} maxDuration={2500} />);

    expect(scheduledDwells()).toEqual([2500]);
    act(() => vi.advanceTimersByTime(2500));
    expect(scheduledDwells()).toEqual([2500, 2500]);
  });

  it("schedules nothing for a single word", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    render(
      <WordRotate
        words={["only real step"]}
        minDuration={1800}
        maxDuration={3200}
      />,
    );

    expect(scheduledDwells()).toEqual([]);
  });

  it("stops scheduling once unmounted", () => {
    vi.spyOn(Math, "random").mockReturnValue(0);
    const { unmount } = render(
      <WordRotate words={["a", "b"]} minDuration={1000} maxDuration={1000} />,
    );

    unmount();
    act(() => vi.advanceTimersByTime(5000));
    expect(scheduledDwells()).toEqual([1000]);
  });
});
