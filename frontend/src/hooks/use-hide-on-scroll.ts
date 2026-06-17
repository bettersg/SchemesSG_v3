"use client";

import { type RefObject, useEffect, useRef, useState } from "react";

const MOBILE_BREAKPOINT = 768;
const SCROLL_SUPPRESSION_MS = 360;
const USER_INTENT_WINDOW_MS = 900;
const IGNORE_SCROLL_SELECTOR = "[data-hide-on-scroll-ignore]";

function getEventElement(event: Event) {
  return event.target instanceof Element ? event.target : null;
}

function shouldIgnoreEvent(
  event: Event,
  scrollContainerRef?: RefObject<HTMLElement | null>,
) {
  const element = getEventElement(event);
  if (element?.closest(IGNORE_SCROLL_SELECTOR)) return true;

  const scrollContainer = scrollContainerRef?.current;
  if (!scrollContainer) return false;

  // When a container is supplied, the hook only tracks that element's own
  // scroll events. Nested scroll regions, drawers, and popovers stay invisible
  // to the hide/reveal logic even if they live inside the same React tree.
  return event.type === "scroll" && event.target !== scrollContainer;
}

// Normalizes window and nested-container scroll events into the same metrics.
function getScrollMetrics(event: Event) {
  const target = event.target;

  if (
    target === document ||
    target === document.documentElement ||
    target === document.body
  ) {
    return {
      maxScrollTop: Math.max(
        document.documentElement.scrollHeight - window.innerHeight,
        0,
      ),
      scrollTop: window.scrollY,
      target,
    };
  }

  if (target instanceof Element) {
    return {
      maxScrollTop: Math.max(target.scrollHeight - target.clientHeight, 0),
      scrollTop: target.scrollTop,
      target,
    };
  }

  return { maxScrollTop: 0, scrollTop: 0, target };
}

/**
 * Hides mobile chrome on deliberate downward scrolling and reveals it on
 * upward scrolling. Scroll intent is tracked separately to ignore layout-
 * induced scroll events caused by the chrome changing height.
 */
export function useHideOnScroll({
  disabled = false,
  resetKey,
  scrollContainerRef,
}: {
  disabled?: boolean;
  resetKey?: string;
  scrollContainerRef?: RefObject<HTMLElement | null>;
} = {}) {
  const [isHidden, setIsHidden] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const isHiddenRef = useRef(false);
  // The capture listener receives scrolls from both page and nested containers.
  const activeScrollTargetRef = useRef<EventTarget | null>(null);
  // Wheel, touch, and keyboard events identify intentional scroll direction.
  const lastIntentAtRef = useRef(0);
  const lastIntentDirectionRef = useRef<"down" | "up" | null>(null);
  const lastTouchYRef = useRef<number | null>(null);
  // Prevents the resulting layout shift from immediately reversing the toggle.
  const suppressToggleUntilRef = useRef(0);

  useEffect(() => {
    isHiddenRef.current = false;
    activeScrollTargetRef.current = null;
    setIsHidden(false);
    setIsScrolled(false);
  }, [resetKey]);

  useEffect(() => {
    if (!disabled) return;
    isHiddenRef.current = false;
    setIsHidden(false);
  }, [disabled]);

  useEffect(() => {
    const markIntent = (direction: "down" | "up") => {
      lastIntentAtRef.current = Date.now();
      lastIntentDirectionRef.current = direction;
    };
    const setHidden = (next: boolean) => {
      if (isHiddenRef.current === next) return;
      isHiddenRef.current = next;
      suppressToggleUntilRef.current = Date.now() + SCROLL_SUPPRESSION_MS;
      setIsHidden(next);
    };
    const onWheel = (event: WheelEvent) => {
      if (shouldIgnoreEvent(event, scrollContainerRef)) return;
      if (Math.abs(event.deltaY) >= 2) {
        markIntent(event.deltaY > 0 ? "down" : "up");
      }
    };
    const onTouchStart = (event: TouchEvent) => {
      if (shouldIgnoreEvent(event, scrollContainerRef)) return;
      lastTouchYRef.current = event.touches[0]?.clientY ?? null;
    };
    const onTouchMove = (event: TouchEvent) => {
      if (shouldIgnoreEvent(event, scrollContainerRef)) return;
      const nextY = event.touches[0]?.clientY;
      const previousY = lastTouchYRef.current;
      if (nextY == null || previousY == null) return;

      const delta = previousY - nextY;
      if (Math.abs(delta) >= 2) markIntent(delta > 0 ? "down" : "up");
      lastTouchYRef.current = nextY;
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (shouldIgnoreEvent(event, scrollContainerRef)) return;
      if (["ArrowDown", "End", "PageDown", " "].includes(event.key)) {
        markIntent("down");
      } else if (["ArrowUp", "Home", "PageUp"].includes(event.key)) {
        markIntent("up");
      }
    };
    const onScroll = (event: Event) => {
      if (shouldIgnoreEvent(event, scrollContainerRef)) return;

      const { maxScrollTop, scrollTop, target } = getScrollMetrics(event);
      if (maxScrollTop <= 0) return;

      const scrollY = Math.max(scrollTop, 0);
      setIsScrolled(window.scrollY > 20 || scrollY > 20);

      if (activeScrollTargetRef.current !== target) {
        // Establish a baseline when scrolling switches to another container.
        activeScrollTargetRef.current = target;
        return;
      }

      const now = Date.now();
      const direction = lastIntentDirectionRef.current;
      const hasRecentIntent =
        now - lastIntentAtRef.current < USER_INTENT_WINDOW_MS;

      if (
        disabled ||
        window.innerWidth >= MOBILE_BREAKPOINT ||
        now < suppressToggleUntilRef.current ||
        !hasRecentIntent ||
        !direction
      ) {
        return;
      }

      const distanceFromBottom = maxScrollTop - scrollY;
      if (scrollY <= 12) setHidden(false);
      else if (direction === "down") setHidden(true);
      // Avoid revealing at the bottom, where browser scroll settling can report up.
      else if (distanceFromBottom > 24) setHidden(false);
    };

    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    window.addEventListener("keydown", onKeyDown);
    document.addEventListener("scroll", onScroll, {
      capture: true,
      passive: true,
    });

    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("scroll", onScroll, { capture: true });
    };
  }, [disabled, scrollContainerRef]);

  return { isHidden, isScrolled };
}
