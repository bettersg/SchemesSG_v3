"use client";

import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import Image from "next/image";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

type ChatSpinnerProps = {
  className?: string;
};

export default function ChatSpinner({ className }: ChatSpinnerProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return (
      <Image
        src="/logo.svg"
        alt=""
        width={32}
        height={32}
        aria-hidden="true"
        className={cn("size-8 object-contain", className)}
      />
    );
  }

  return (
    <DotLottieReact
      className={cn("size-8", className)}
      src="https://lottie.host/f16d88bc-aee3-4c2f-b50f-fa9f3750e242/je06uPGeC8.lottie"
      loop
      autoplay
    />
  );
}
