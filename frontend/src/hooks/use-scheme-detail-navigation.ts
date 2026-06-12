"use client";

import {
  type RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export type SchemeDetailAnchor = {
  id: string;
  label: string;
};

const ANCHOR_SELECTION_LOCK_MS = 1000;

/**
 * Measures the complete sticky scheme header and exposes its height as both
 * React state and a CSS variable used by section scroll margins.
 */
export function useSchemeDetailStickyOffset(
  headerRef: RefObject<HTMLDivElement | null>,
) {
  const [offset, setOffset] = useState(208);

  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    const updateOffset = () => {
      const nextOffset = Math.ceil(header.getBoundingClientRect().height) + 16;
      setOffset(nextOffset);
      // Keeps CSS anchor offsets synchronized with responsive header wrapping.
      document.documentElement.style.setProperty(
        "--scheme-detail-sticky-offset",
        `${nextOffset}px`,
      );
    };

    updateOffset();
    const observer = new ResizeObserver(updateOffset);
    observer.observe(header);
    window.addEventListener("resize", updateOffset);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateOffset);
      document.documentElement.style.removeProperty(
        "--scheme-detail-sticky-offset",
      );
    };
  }, [headerRef]);

  return offset;
}

/**
 * Synchronizes the selected section tab with scrolling and hash navigation.
 * Observer updates handle manual scrolling; selectAnchor handles tab presses.
 */
export function useSchemeSectionNavigation({
  anchors,
  stickyOffset,
  headerRef,
}: {
  anchors: SchemeDetailAnchor[];
  stickyOffset: number;
  headerRef: RefObject<HTMLDivElement | null>;
}) {
  const [activeAnchor, setActiveAnchor] = useState(anchors[0]?.id ?? "");
  const selectionLockRef = useRef<string | null>(null);
  const selectionLockTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );

  useEffect(() => {
    setActiveAnchor(anchors[0]?.id ?? "");
  }, [anchors]);

  useEffect(() => {
    if (anchors.length <= 1) return;

    const sections = anchors
      .map(({ id }) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section));
    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // A clicked tab stays selected while smooth scrolling passes other sections.
        if (selectionLockRef.current) return;

        const scrollContainer = headerRef.current?.closest(".overflow-y-auto");
        const isAtBottom =
          scrollContainer &&
          scrollContainer.scrollHeight -
            scrollContainer.scrollTop -
            scrollContainer.clientHeight <
            32;

        if (isAtBottom) {
          // The final short section may never cross the observer threshold.
          setActiveAnchor(anchors.at(-1)?.id ?? "");
          return;
        }

        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible?.target.id) setActiveAnchor(visible.target.id);
      },
      {
        root: null,
        // Only the reading area below the sticky header counts as visible.
        rootMargin: `-${stickyOffset}px 0px -60% 0px`,
        threshold: [0.1, 0.4, 0.7],
      },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [anchors, headerRef, stickyOffset]);

  useEffect(
    () => () => {
      if (selectionLockTimerRef.current) {
        clearTimeout(selectionLockTimerRef.current);
      }
    },
    [],
  );

  const selectAnchor = useCallback((id: string) => {
    const section = document.getElementById(id);
    if (!section) return;

    if (selectionLockTimerRef.current) {
      clearTimeout(selectionLockTimerRef.current);
    }
    selectionLockRef.current = id;
    setActiveAnchor(id);
    window.history.replaceState(null, "", `#${id}`);
    section.scrollIntoView({ behavior: "smooth", block: "start" });
    // Release the lock after smooth scrolling has settled.
    selectionLockTimerRef.current = setTimeout(() => {
      selectionLockRef.current = null;
      selectionLockTimerRef.current = null;
    }, ANCHOR_SELECTION_LOCK_MS);
  }, []);

  return { activeAnchor, selectAnchor };
}
