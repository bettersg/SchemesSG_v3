"use client";

import { TextShimmerWave } from "@/components/animations/text-shimmer-wave";
import { cn } from "@/lib/utils";

type StatusTextShimmerProps = {
  children: string;
  className?: string;
};

export function StatusTextShimmer({
  children,
  className,
}: StatusTextShimmerProps) {
  return (
    <TextShimmerWave
      duration={1.2}
      spread={1.4}
      className={cn(
        "[--base-color:var(--schemes-status-info-text)] [--base-gradient-color:var(--schemes-blue-400)]",
        className,
      )}
    >
      {children}
    </TextShimmerWave>
  );
}
