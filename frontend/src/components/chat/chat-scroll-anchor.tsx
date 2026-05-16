"use client";

import { ArrowDown } from "lucide-react";

type ChatScrollAnchorProps = {
  show: boolean;
  onClick: () => void;
  hasQuickReplies?: boolean;
};

export function ChatScrollAnchor({
  show,
  onClick,
  hasQuickReplies = false,
}: ChatScrollAnchorProps) {
  if (!show) return null;

  return (
    <div
      className={`pointer-events-none absolute right-0 left-0 z-10 flex justify-end px-4 ${
        hasQuickReplies ? "bottom-[9rem]" : "bottom-[6rem]"
      }`}
    >
      <button
        type="button"
        onClick={onClick}
        className="pointer-events-auto inline-flex h-9 w-9 items-center justify-center gap-1.5 rounded-full bg-white/70 p-1.5 text-xs font-semibold text-(--schemes-blue-600) shadow-[0_4px_14px_rgba(24,95,165,0.08)] backdrop-blur-md transition-[background-color,border-color,color,box-shadow,transform] hover:bg-(--schemes-blue-50)/85 hover:text-(--schemes-blue-900) hover:shadow-[0_6px_18px_rgba(24,95,165,0.12)]"
      >
        <ArrowDown size={16} strokeWidth={2} />
      </button>
    </div>
  );
}
