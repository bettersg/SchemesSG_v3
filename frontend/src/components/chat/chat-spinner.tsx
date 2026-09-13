"use client";

import { DotLottieReact, setWasmUrl } from "@lottiefiles/dotlottie-react";
import Image from "next/image";
import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

// Without this the player fetches its wasm runtime from a CDN and renders
// nothing when that CDN is blocked. Vendored by scripts/copy-lottie-wasm.mjs.
setWasmUrl("/dotlottie-player.wasm");

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
      // Self-hosted rather than pulled from lottie.host: this spinner sits on
      // the critical path of "show something immediately", so nothing it needs
      // should come from a third-party origin.
      src="/chat-spinner.lottie"
      loop
      autoplay
    />
  );
}
