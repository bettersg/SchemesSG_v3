"use client";
import { useRef, KeyboardEvent } from "react";
import { StopGeneratingButton } from "@/components/chat/stop-generating-button";
import { Maximize2, Minimize2, ShieldCheck } from "lucide-react";
import { useAutoGrowTextarea } from "@/hooks/use-auto-grow-textarea";

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
  const { expanded, setExpanded, canExpand, multiline, reset } =
    useAutoGrowTextarea(ref, value, {
      lineHeight: 24,
      collapsedMaxHeight: 120,
      expandedMaxHeight: 360,
    });

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    onValueChange("");
    reset();
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="px-4 pb-3 pt-1 shrink-0 sm:px-5">
      {/* Single line: a pill with the text and send button on one row.
          Multi-line: a rounded rectangle with the text on top and send below.
          The expand/collapse toggle pins top-right once content overflows. */}
      <div
        className={`relative border border-(--schemes-border) bg-white px-3 shadow-[0_2px_12px_rgba(15,23,42,0.06)] transition-[border-color,box-shadow] focus-within:border-(--schemes-blue-100) focus-within:shadow-[0_4px_18px_rgba(15,23,42,0.10)] ${
          multiline
            ? "flex flex-col rounded-3xl py-2.5"
            : "flex items-center gap-2 rounded-full py-1.5"
        }`}
      >
        {(canExpand || expanded) && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-label={expanded ? "Collapse input" : "Expand input"}
            className="absolute right-2 top-2 z-10 flex size-8 items-center justify-center rounded-full text-(--schemes-muted) transition-colors hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)"
          >
            {expanded ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </button>
        )}
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => onValueChange(e.target.value)}
          onKeyDown={handleKey}
          disabled={isGenerating}
          aria-disabled={isGenerating}
          placeholder="Ask a follow-up question…"
          rows={1}
          className={`thin-scrollbar min-h-6 resize-none overscroll-contain bg-transparent px-1 py-0 text-sm leading-6 text-(--schemes-ink) placeholder:text-(--schemes-muted) focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60 ${
            multiline ? "w-full shrink-0 pr-8" : "flex-1"
          }`}
        />
        {!multiline ? (
          <StopGeneratingButton
            isGenerating={isGenerating}
            canSend={!!value.trim()}
            onSend={handleSend}
            onStop={onStop}
          />
        ) : (
          <div className="mt-2 flex justify-end">
            <StopGeneratingButton
              isGenerating={isGenerating}
              canSend={!!value.trim()}
              onSend={handleSend}
              onStop={onStop}
            />
          </div>
        )}
      </div>
      <p className="mt-2 flex items-center justify-center gap-1 text-center text-[10px] text-(--schemes-muted-light)">
        <ShieldCheck size={9} strokeWidth={2} />
        Anonymous · No personal data stored
      </p>
    </div>
  );
}
