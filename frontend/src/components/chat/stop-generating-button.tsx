"use client";

import {
  productButtonSolidBlue,
} from "@/lib/design-system/product-styles";
import { SendHorizontal } from "lucide-react";

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
      className={`${productButtonSolidBlue} size-9 shrink-0 p-0`}
    >
      <SendHorizontal size={17} strokeWidth={1.9} />
    </button>
  );
}
