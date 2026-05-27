"use client";

import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

interface ShinyTextProps {
  disabled?: boolean;
  speed?: number;
  className?: string;
  color?: string;
  shineColor?: string;
  children: ReactNode;
}

export default function ShinyText({
  disabled = false,
  speed = 5,
  className = "",
  color = "var(--schemes-status-info-text)",
  shineColor = "var(--schemes-blue-400)",
  children,
}: ShinyTextProps) {
  const style = {
    "--shiny-text-base": color,
    "--shiny-text-shine": shineColor,
    animationDuration: `${speed}s`,
    backgroundImage:
      "linear-gradient(120deg, var(--shiny-text-base) 40%, var(--shiny-text-shine) 50%, var(--shiny-text-base) 60%)",
    backgroundSize: "200% 100%",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    WebkitTextFillColor: "transparent",
    animation: disabled
      ? "none"
      : `schemes-shiny-text ${speed}s linear infinite`,
  } as CSSProperties;

  return (
    <span
      className={cn(
        "inline-block bg-clip-text text-transparent",
        className,
      )}
      style={style}
    >
      {children}
    </span>
  );
}
