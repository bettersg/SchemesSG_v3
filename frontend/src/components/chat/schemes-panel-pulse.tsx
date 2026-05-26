"use client";

import { cn } from "@/lib/utils";

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
  return (
    <span className={cn("relative inline-flex", className)}>
      {active && (
        <span className="absolute inset-0 rounded-lg border border-(--schemes-blue-400) opacity-75 animate-ping" />
      )}
      <span className="relative inline-flex">{children}</span>
    </span>
  );
}
