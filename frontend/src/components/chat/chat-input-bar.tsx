"use client";
import { useRef, KeyboardEvent } from "react";
import { StopGeneratingButton } from "@/components/chat/stop-generating-button";
import { Maximize2, Minimize2, ShieldCheck } from "lucide-react";
import { useAutoGrowTextarea } from "@/hooks/use-auto-grow-textarea";
import {
  productComposerChatSurface,
  productComposerExpandButton,
  productComposerMultiline,
  productComposerSingleLine,
  productComposerSurface,
  productComposerTextarea,
  productComposerTextareaMultiline,
  productComposerTextareaSingleLine,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";

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
        className={cn(
          productComposerSurface,
          productComposerChatSurface,
          multiline
            ? cn(productComposerMultiline, "py-2.5")
            : cn(productComposerSingleLine, "gap-2 py-1.5"),
        )}
      >
        {(canExpand || expanded) && (
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            aria-label={expanded ? "Collapse input" : "Expand input"}
            className={cn(
              productComposerExpandButton,
              "right-2 top-2 text-(--schemes-muted) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)",
            )}
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
          className={cn(
            productComposerTextarea,
            "min-h-6 px-1 py-0 text-sm leading-6 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60",
            multiline
              ? productComposerTextareaMultiline
              : productComposerTextareaSingleLine,
          )}
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
