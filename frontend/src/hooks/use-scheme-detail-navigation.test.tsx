import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  useSchemeDetailStickyOffset,
  useSchemeSectionNavigation,
} from "./use-scheme-detail-navigation";

function makeIntersectionEntry(
  target: Element,
  intersectionRatio: number,
): IntersectionObserverEntry {
  const bounds = target.getBoundingClientRect();
  return {
    boundingClientRect: bounds,
    intersectionRatio,
    intersectionRect: bounds,
    isIntersecting: true,
    rootBounds: null,
    target,
    time: 0,
  };
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  window.history.replaceState(null, "", "/");
  document.documentElement.style.removeProperty(
    "--scheme-detail-sticky-offset",
  );
  document.body.replaceChildren();
});

describe("scheme detail navigation", () => {
  it("tracks the sticky header height and removes its CSS offset on cleanup", () => {
    let resizeCallback: ResizeObserverCallback = () => undefined;
    const disconnect = vi.fn();
    const observe = vi.fn();
    vi.stubGlobal(
      "ResizeObserver",
      class {
        constructor(callback: ResizeObserverCallback) {
          resizeCallback = callback;
        }
        disconnect = disconnect;
        observe = observe;
        unobserve = vi.fn();
      },
    );
    const header = document.createElement("div");
    let height = 144;
    header.getBoundingClientRect = () => ({ height }) as DOMRect;
    const { result, unmount } = renderHook(() =>
      useSchemeDetailStickyOffset({ current: header }),
    );

    expect(result.current).toBe(160);
    expect(
      document.documentElement.style.getPropertyValue(
        "--scheme-detail-sticky-offset",
      ),
    ).toBe("160px");
    height = 200;
    act(() => resizeCallback([], {} as ResizeObserver));
    expect(result.current).toBe(216);

    unmount();
    expect(
      document.documentElement.style.getPropertyValue(
        "--scheme-detail-sticky-offset",
      ),
    ).toBe("");
  });

  it("selects anchors and follows the most visible section after scrolling", () => {
    vi.useFakeTimers();
    let intersectionCallback: IntersectionObserverCallback = () => undefined;
    const disconnect = vi.fn();
    const observe = vi.fn();
    const observer = { disconnect, observe } as unknown as IntersectionObserver;
    vi.stubGlobal(
      "IntersectionObserver",
      class {
        constructor(callback: IntersectionObserverCallback) {
          intersectionCallback = callback;
        }
        disconnect = disconnect;
        observe = observe;
        takeRecords = () => [];
        unobserve = vi.fn();
        root = null;
        rootMargin = "0px";
        thresholds = [];
      },
    );
    const overview = document.createElement("section");
    overview.id = "overview";
    const agency = document.createElement("section");
    agency.id = "agency";
    agency.scrollIntoView = vi.fn();
    document.body.append(overview, agency);
    const anchors = [
      { id: "overview", label: "Overview" },
      { id: "agency", label: "Agency details" },
    ];
    const { result } = renderHook(() =>
      useSchemeSectionNavigation({
        anchors,
        stickyOffset: 160,
        headerRef: { current: document.createElement("div") },
      }),
    );

    expect(result.current.activeAnchor).toBe("overview");
    act(() => result.current.selectAnchor("agency"));
    expect(result.current.activeAnchor).toBe("agency");
    expect(window.location.hash).toBe("#agency");
    expect(agency.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });

    act(() => {
      vi.runAllTimers();
      intersectionCallback(
        [
          makeIntersectionEntry(overview, 0.8),
          makeIntersectionEntry(agency, 0.2),
        ],
        observer,
      );
    });
    expect(result.current.activeAnchor).toBe("overview");
  });
});
