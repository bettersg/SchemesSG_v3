"use client";

import { Button, Tooltip, type PressEvent } from "@heroui/react";
import { motion } from "framer-motion";
import { useRef, useState } from "react";
import {
  productButtonSecondary,
  productButtonSm,
} from "@/lib/design-system/product-styles";
import { duration, stagger } from "@/lib/design-system/motion";

export type FollowUpSuggestion = {
  label: string;
  value: string;
};

type FollowUpSuggestionsProps = {
  suggestions: FollowUpSuggestion[];
  onSelect: (value: string) => void;
};

type TooltipPlacement =
  | "top"
  | "bottom"
  | "top start"
  | "top end"
  | "bottom start"
  | "bottom end";

export function FollowUpSuggestions({
  suggestions,
  onSelect,
}: FollowUpSuggestionsProps) {
  const [placements, setPlacements] = useState<
    Record<string, TooltipPlacement>
  >({});
  const [openTooltip, setOpenTooltip] = useState<string | null>(null);
  const longPressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const suppressClickRef = useRef(false);

  if (!suggestions.length) return null;

  const clearLongPressTimer = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  };

  const getTooltipPlacement = (target: Element): TooltipPlacement => {
    const rect = target.getBoundingClientRect();
    const vertical = rect.top < 150 ? "bottom" : "top";

    if (rect.left < 48) {
      return `${vertical} start` as TooltipPlacement;
    }
    if (window.innerWidth - rect.right < 48) {
      return `${vertical} end` as TooltipPlacement;
    }
    return vertical;
  };

  const showTooltip = (suggestion: FollowUpSuggestion, target: Element) => {
    setPlacements((prev) => ({
      ...prev,
      [suggestion.label]: getTooltipPlacement(target),
    }));
    setOpenTooltip(suggestion.label);
  };

  const hideTooltip = (label: string) => {
    clearLongPressTimer();
    setOpenTooltip((current) => (current === label ? null : current));
  };

  const handleSelect = (event: PressEvent, suggestion: FollowUpSuggestion) => {
    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      return;
    }
    onSelect(suggestion.value);
  };

  return (
    <div className="no-scrollbar flex shrink-0 flex-row flex-nowrap gap-2 overflow-x-auto overflow-y-hidden px-4 py-2 sm:flex-wrap sm:overflow-visible">
      {suggestions.slice(0, 3).map((suggestion, index) => (
        <motion.div
          key={suggestion.label}
          className="shrink-0"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * stagger, duration: duration.state }}
        >
          <Tooltip
            closeDelay={0}
            delay={250}
            isOpen={openTooltip === suggestion.label}
            onOpenChange={(isOpen) => {
              setOpenTooltip(isOpen ? suggestion.label : null);
            }}
          >
            <Tooltip.Trigger>
              <Button
                variant="outline"
                aria-label={`${suggestion.label}: ${suggestion.value}`}
                onPress={(event) => handleSelect(event, suggestion)}
                onFocus={(event) =>
                  showTooltip(suggestion, event.currentTarget)
                }
                onBlur={() => hideTooltip(suggestion.label)}
                onMouseEnter={(event) => {
                  showTooltip(suggestion, event.currentTarget);
                }}
                onMouseLeave={() => hideTooltip(suggestion.label)}
                onPointerDown={(event) => {
                  if (event.pointerType === "mouse") return;
                  clearLongPressTimer();
                  suppressClickRef.current = false;
                  const target = event.currentTarget;
                  longPressTimerRef.current = setTimeout(() => {
                    suppressClickRef.current = true;
                    showTooltip(suggestion, target);
                  }, 500);
                }}
                onPointerUp={(event) => {
                  clearLongPressTimer();
                  if (event.pointerType === "mouse") return;
                  if (!suppressClickRef.current) return;
                  setTimeout(() => {
                    hideTooltip(suggestion.label);
                    suppressClickRef.current = false;
                  }, 900);
                }}
                onPointerCancel={() => {
                  clearLongPressTimer();
                  hideTooltip(suggestion.label);
                }}
                onContextMenu={(event) => {
                  if (suppressClickRef.current) {
                    event.preventDefault();
                  }
                }}
                className={`${productButtonSecondary} ${productButtonSm} shrink-0 cursor-pointer touch-manipulation whitespace-nowrap rounded-full`}
              >
                {suggestion.label}
              </Button>
            </Tooltip.Trigger>
            <Tooltip.Content
              offset={8}
              placement={placements[suggestion.label] ?? "top"}
              className="max-w-[min(360px,calc(100vw-32px))] rounded-xl border border-(--schemes-blue-100) bg-white px-3 py-2 text-xs font-medium leading-relaxed text-(--schemes-blue-900) shadow-[0_8px_24px_rgba(24,95,165,0.14)]"
            >
              <Tooltip.Arrow className="fill-white text-(--schemes-blue-100)" />
              <span className="mb-1 block text-[10px] font-semibold tracking-widest text-(--schemes-blue-600) uppercase">
                {suggestion.label}
              </span>
              {suggestion.value}
            </Tooltip.Content>
          </Tooltip>
        </motion.div>
      ))}
    </div>
  );
}
