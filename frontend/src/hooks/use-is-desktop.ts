"use client";

import { useEffect, useState } from "react";

// True on tablet/desktop (>=768px), matching the app's `md` breakpoint. Drives
// the overlay affordance for pickers: a popover on desktop, a bottom-sheet
// drawer on mobile where popover rows are too small to tap reliably.
export function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const update = () => setIsDesktop(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  return isDesktop;
}
