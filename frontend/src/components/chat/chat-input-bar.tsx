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
    <div className="px-4 pb-3 pt-1 shrink-0 sm:px-5">
      <div className="flex items-end gap-2 rounded-3xl border border-(--schemes-border) bg-white px-2 py-2 pl-4 shadow-[0_2px_12px_rgba(15,23,42,0.06)] transition-[border-color,box-shadow] focus-within:border-(--schemes-blue-100) focus-within:shadow-[0_4px_18px_rgba(15,23,42,0.10)]">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={isGenerating}
          aria-disabled={isGenerating}
          placeholder="Ask a follow-up question…"
          rows={1}
          className="thin-scrollbar flex-1 resize-none self-center overscroll-contain bg-transparent focus-visible:outline-none text-sm text-(--schemes-ink) placeholder:text-(--schemes-muted) leading-relaxed min-h-[24px] max-h-[72px] disabled:cursor-not-allowed disabled:opacity-60"
        />
        <StopGeneratingButton
          isGenerating={isGenerating}
          canSend={!!value.trim()}
          onSend={handleSend}
          onStop={onStop}
        />
      </div>
      <p className="mt-2 flex items-center justify-center gap-1 text-center text-[10px] text-(--schemes-muted-light)">
        <ShieldCheck size={9} strokeWidth={2} />
        Anonymous · No personal data stored
      </p>
    </div>
  );
}
