"use client";

import { productButtonSolidBlue } from "@/lib/design-system/product-styles";
import { ArrowRight } from "lucide-react";

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
        className={`${productButtonSolidBlue} size-9 shrink-0 p-0`}
      >
        <span className="h-3 w-3 rounded-[3px] bg-white" />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onSend}
      disabled={!canSend}
      aria-label="Send message"
      className="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-400 text-neutral-900 shadow-sm transition-colors duration-200 hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-45"
    >
      <ArrowRight className="h-4 w-4" />
    </button>
  );
}
