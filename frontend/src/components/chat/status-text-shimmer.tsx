"use client";

import ShinyText from "@/components/animations/shiny-text";
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
    <ShinyText
      speed={2}
      color="var(--schemes-status-info-text)"
      shineColor="var(--schemes-blue-400)"
      className={cn("font-semibold", className)}
    >
      {children}
    </ShinyText>
  );
}
