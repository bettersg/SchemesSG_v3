import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useHideOnScroll } from "./use-hide-on-scroll";

const originalInnerWidth = Object.getOwnPropertyDescriptor(
  window,
  "innerWidth",
);

afterEach(() => {
  vi.useRealTimers();
  if (originalInnerWidth) {
    Object.defineProperty(window, "innerWidth", originalInnerWidth);
  }
  document.body.replaceChildren();
});

describe("useHideOnScroll", () => {
  it("hides on intentional mobile downward scroll and reveals on upward scroll", () => {
    vi.useFakeTimers();
    vi.setSystemTime(1_000);
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 390,
    });
    const container = document.createElement("div");
    Object.defineProperties(container, {
      scrollHeight: { configurable: true, value: 1_000 },
      clientHeight: { configurable: true, value: 200 },
    });
    document.body.append(container);
    const ref = { current: container };
    const { result } = renderHook(() =>
      useHideOnScroll({ scrollContainerRef: ref }),
    );

    act(() => {
      container.scrollTop = 80;
      window.dispatchEvent(new WheelEvent("wheel", { deltaY: 20 }));
      container.dispatchEvent(new Event("scroll"));
    });
    expect(result.current).toEqual({ isHidden: false, isScrolled: true });

    act(() => {
      container.scrollTop = 140;
      container.dispatchEvent(new Event("scroll"));
    });
    expect(result.current.isHidden).toBe(true);

    act(() => {
      vi.advanceTimersByTime(400);
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
      container.scrollTop = 80;
      container.dispatchEvent(new Event("scroll"));
    });
    expect(result.current.isHidden).toBe(false);
  });

  it("resets hidden and scrolled state when its navigation key changes", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 390,
    });
    const container = document.createElement("div");
    Object.defineProperties(container, {
      scrollHeight: { configurable: true, value: 1_000 },
      clientHeight: { configurable: true, value: 200 },
    });
    document.body.append(container);
    const ref = { current: container };
    const { result, rerender } = renderHook(
      ({ resetKey }) => useHideOnScroll({ resetKey, scrollContainerRef: ref }),
      { initialProps: { resetKey: "first" } },
    );

    act(() => {
      container.scrollTop = 100;
      window.dispatchEvent(new WheelEvent("wheel", { deltaY: 20 }));
      container.dispatchEvent(new Event("scroll"));
      container.dispatchEvent(new Event("scroll"));
    });
    expect(result.current.isScrolled).toBe(true);

    rerender({ resetKey: "second" });
    expect(result.current).toEqual({ isHidden: false, isScrolled: false });
  });
});
