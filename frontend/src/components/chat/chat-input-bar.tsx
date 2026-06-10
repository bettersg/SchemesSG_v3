"use client";
import { useEffect, useRef, KeyboardEvent } from "react";
import { StopGeneratingButton } from "@/components/chat/stop-generating-button";
import { ShieldCheck } from "lucide-react";

interface ChatInputBarProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isGenerating: boolean;
  value: string;
  onValueChange: (value: string) => void;
}

export default function ChatInputBar({
  onSend,
  onStop,
  isGenerating,
  value,
  onValueChange,
}: ChatInputBarProps) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const MAX_HEIGHT = 72;

  useEffect(() => {
    if (!ref.current) return;
    ref.current.style.height = "auto";
    ref.current.style.height =
      Math.min(ref.current.scrollHeight, MAX_HEIGHT) + "px";
  }, [value]);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    onValueChange("");
    if (ref.current) {
      ref.current.style.height = "auto";
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-white border-t border-(--schemes-border) px-3 py-2.5 shrink-0">
      <div className="flex gap-2.5 items-end bg-(--schemes-bg) border border-(--schemes-border) rounded-xl px-3.5 py-2 focus-within:border-(--schemes-blue-600) focus-within:ring-2 focus-within:ring-(--schemes-blue-400) focus-within:bg-white transition-[border-color,box-shadow,background-color]">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={isGenerating}
          aria-disabled={isGenerating}
          placeholder="Ask a follow-up question…"
          rows={1}
          className="thin-scrollbar flex-1 resize-none overscroll-contain bg-transparent focus-visible:outline-none text-sm text-(--schemes-ink) placeholder:text-(--schemes-muted) leading-relaxed min-h-[24px] max-h-[72px] disabled:cursor-not-allowed disabled:opacity-60"
        />
        <StopGeneratingButton
          isGenerating={isGenerating}
          canSend={!!value.trim()}
          onSend={handleSend}
          onStop={onStop}
        />
      </div>
      <p className="text-center text-[10px] text-(--schemes-muted) mt-1.5 flex items-center justify-center gap-1">
        <ShieldCheck size={9} strokeWidth={2} />
        Anonymous · No personal data stored
      </p>
    </div>
  );
}
