"use client";

import {
  productButtonCompact,
  productButtonOutlineNeutral,
} from "@/lib/design-system/product-styles";
import { Trans, useLingui } from "@lingui/react/macro";

type StreamingErrorCardProps = {
  message?: string;
  onNewChat: () => void;
};

export function StreamingErrorCard({
  message,
  onNewChat,
}: StreamingErrorCardProps) {
  const { t } = useLingui();
  const displayMessage = message ?? t({ message: "Send your question again.", comment: "Default error message when the chat stream fails" });

  return (
    <div
      role="alert"
      className="mx-4 mb-2 rounded-xl border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) p-3 text-sm text-(--schemes-status-alert-text)"
    >
      <p className="font-semibold"><Trans comment="Error card heading when the chat response fails">The answer stopped partway</Trans></p>
      <p className="mt-1 text-(--schemes-muted)">{displayMessage}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onNewChat}
          className={`${productButtonOutlineNeutral} ${productButtonCompact}`}
        >
          <Trans comment="Button in the error card to start a new conversation">Start new chat</Trans>
        </button>
      </div>
    </div>
  );
}
