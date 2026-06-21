"use client";

import { ArrowRight } from "lucide-react";
import { productComposerSendButton } from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";

type StopGeneratingButtonProps = {
  isGenerating: boolean;
  canSend: boolean;
  onSend: () => void;
  onStop: () => void;
};

export function StopGeneratingButton({
  isGenerating,
  canSend,
  onSend,
  onStop,
}: StopGeneratingButtonProps) {
  if (isGenerating) {
    return (
      <button
        type="button"
        onClick={onStop}
        aria-label="Stop generating"
        className={cn(productComposerSendButton, "size-9")}
      >
        <span className="h-3 w-3 rounded-[3px] bg-neutral-800" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onSend}
      disabled={!canSend}
      aria-label="Send message"
      className={cn(productComposerSendButton, "size-9")}
    >
      <ArrowRight className="h-4 w-4" />
    </button>
  );
}
