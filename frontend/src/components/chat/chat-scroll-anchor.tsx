"use client";

import { ArrowDown } from "lucide-react";

type ChatScrollAnchorProps = {
  show: boolean;
  onClick: () => void;
};

export function ChatScrollAnchor({ show, onClick }: ChatScrollAnchorProps) {
  if (!show) return null;

  // Sticky to the bottom of the scroll viewport (not the scrolled content), so
  // it always hovers a fixed gap above the composer regardless of message
  // length or quick-reply height — and centered, the convention for a
  // jump-to-latest control (Gemini, ChatGPT, Slack).
  return (
    <div className="pointer-events-none sticky bottom-2 z-10 -mt-9 flex justify-center">
      <button
        type="button"
        onClick={onClick}
        aria-label="Scroll to latest"
        className="pointer-events-auto inline-flex size-9 items-center justify-center rounded-full border border-(--schemes-border) bg-white/85 text-(--schemes-blue-600) shadow-[0_4px_14px_rgba(24,95,165,0.10)] backdrop-blur-md transition-[background-color,color,box-shadow] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)"
      >
        <ArrowDown size={16} strokeWidth={2} />
      </button>
    </div>
  );
}
