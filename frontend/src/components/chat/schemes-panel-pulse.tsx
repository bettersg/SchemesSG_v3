"use client";

import { cn } from "@/lib/utils";
import { useReducedMotion } from "framer-motion";

type SchemesPanelPulseProps = {
  active: boolean;
  children: React.ReactNode;
  className?: string;
};

export function SchemesPanelPulse({
  active,
  children,
  className,
}: SchemesPanelPulseProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <span className={cn("relative inline-flex", className)}>
      {active && !shouldReduceMotion && (
        <span className="absolute inset-0 rounded-lg border border-(--schemes-blue-400) opacity-75 animate-ping" />
      )}
      <span className="relative inline-flex">{children}</span>
      {active && shouldReduceMotion && (
        <>
          <span
            aria-hidden="true"
            className="absolute -right-2 -top-1 size-2 rounded-full bg-(--schemes-blue-400)"
          />
          <span className="sr-only">New schemes available</span>
        </>
      )}
    </span>
  );
}
