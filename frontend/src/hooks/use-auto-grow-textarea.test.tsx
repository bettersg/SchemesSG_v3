import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useAutoGrowTextarea } from "./use-auto-grow-textarea";

describe("useAutoGrowTextarea", () => {
  it("sizes to content, exposes overflow, and resets when content shrinks", () => {
    const textarea = document.createElement("textarea");
    textarea.placeholder = "A placeholder that could wrap";
    textarea.style.minHeight = "24px";
    let naturalHeight = 180;
    Object.defineProperty(textarea, "scrollHeight", {
      configurable: true,
      get: () => naturalHeight,
    });
    const ref = { current: textarea };
    const { result, rerender } = renderHook(
      ({ value }) =>
        useAutoGrowTextarea(ref, value, {
          lineHeight: 24,
          collapsedMaxHeight: 120,
          expandedMaxHeight: 360,
        }),
      { initialProps: { value: "Long content" } },
    );

    expect(result.current).toMatchObject({
      expanded: false,
      canExpand: true,
      multiline: true,
    });
    expect(textarea.style.height).toBe("120px");
    expect(textarea.style.minHeight).toBe("24px");
    expect(textarea.placeholder).toBe("A placeholder that could wrap");

    act(() => result.current.setExpanded(true));
    expect(textarea.style.height).toBe("180px");

    naturalHeight = 24;
    rerender({ value: "Short" });
    expect(result.current).toMatchObject({
      expanded: false,
      canExpand: false,
      multiline: false,
    });
    expect(textarea.style.height).toBe("24px");

    act(() => result.current.reset());
    expect(textarea.style.height).toBe("auto");
  });

  it("does nothing until the textarea ref is available", () => {
    const { result } = renderHook(() =>
      useAutoGrowTextarea({ current: null }, "content", {
        lineHeight: 24,
        collapsedMaxHeight: 120,
        expandedMaxHeight: 360,
      }),
    );

    expect(result.current).toMatchObject({
      expanded: false,
      canExpand: false,
      multiline: false,
    });
  });
});
