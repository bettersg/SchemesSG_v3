"use client";

import {
  productButtonSm,
  productButtonTertiary,
} from "@/lib/design-system/product-styles";

type StreamingErrorCardProps = {
  message?: string;
  onNewChat: () => void;
};

export function StreamingErrorCard({
  message = "Something went wrong while generating a response.",
  onNewChat,
}: StreamingErrorCardProps) {
  return (
    <div className="mx-4 mb-2 rounded-xl border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) p-3 text-sm text-(--schemes-status-alert-text)">
      <p className="font-semibold">Unable to finish response</p>
      <p className="mt-1 text-(--schemes-muted)">{message}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onNewChat}
          className={`${productButtonTertiary} ${productButtonSm}`}
        >
          Start new chat
        </button>
      </div>
    </div>
  );
}
