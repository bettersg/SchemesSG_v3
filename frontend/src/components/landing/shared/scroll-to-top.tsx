"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useState } from "react";
import { REVEAL_CHROME_EVENT } from "@/hooks/use-hide-on-scroll";

/**
 * Back-to-top button for the long reference pages (/developers, /privacy,
 * /terms) on mobile, where the contents strip scrolls away with the page. On lg
 * the contents sidebar stays pinned, so the button is hidden there. Styled to
 * match the chat's jump-to-latest control.
 */
export function ScrollToTop() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // One viewport down: before that the contents strip is still within reach.
    const update = () => setShow(window.scrollY > window.innerHeight);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  if (!show) return null;

  return (
    <button
      type="button"
      onClick={() => {
        const reduce = window.matchMedia?.(
          "(prefers-reduced-motion: reduce)",
        ).matches;
        window.dispatchEvent(new Event(REVEAL_CHROME_EVENT));
        window.scrollTo({ top: 0, behavior: reduce ? "instant" : "smooth" });
      }}
      aria-label="Scroll to top"
      className="fixed right-4 bottom-[max(1rem,env(safe-area-inset-bottom))] z-30 inline-flex size-11 items-center justify-center rounded-full border border-(--schemes-border) bg-white/85 text-(--schemes-blue-600) shadow-[0_4px_14px_rgba(24,95,165,0.10)] backdrop-blur-md transition-[background-color,color,box-shadow] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) lg:hidden"
    >
      <ArrowUp size={16} strokeWidth={2} />
    </button>
  );
}
