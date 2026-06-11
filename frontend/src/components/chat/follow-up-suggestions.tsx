"use client";

import { Button, ScrollShadow, Tooltip } from "@heroui/react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  productButtonCompact,
  productButtonOutlineBlue,
  productCardHeading,
} from "@/lib/design-system/product-styles";
import { duration, stagger } from "@/lib/design-system/motion";
import { cn } from "@/lib/utils";

export type FollowUpSuggestion = {
  label: string;
  value: string;
};

type FollowUpSuggestionsProps = {
  suggestions: FollowUpSuggestion[];
  onSelect: (value: string) => void;
};

export function FollowUpSuggestions({
  suggestions,
  onSelect,
}: FollowUpSuggestionsProps) {
  // Tooltips that preview the full follow-up are a hover affordance. On touch
  // there's no hover and no reliable dismiss, so we skip them entirely and let
  // the chip send on tap. The aria-label still carries the full value for AT.
  const [hoverCapable, setHoverCapable] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(hover: hover) and (pointer: fine)");
    const update = () => setHoverCapable(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  if (!suggestions.length) return null;

  return (
    <ScrollShadow
      orientation="horizontal"
      className="no-scrollbar flex shrink-0 flex-row flex-nowrap gap-2 overflow-x-auto overflow-y-hidden px-4 py-2 sm:flex-wrap sm:overflow-visible sm:px-5"
    >
      {suggestions.map((suggestion, index) => {
        const chip = (
          <Button
            variant="outline"
            aria-label={`${suggestion.label}: ${suggestion.value}`}
            onPress={() => onSelect(suggestion.value)}
            className={`${productButtonOutlineBlue} ${productButtonCompact} shrink-0 cursor-pointer touch-manipulation whitespace-nowrap rounded-full`}
          >
            {suggestion.label}
          </Button>
        );

        return (
          <motion.div
            key={suggestion.label}
            className="shrink-0"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * stagger, duration: duration.state }}
          >
            {hoverCapable ? (
              <Tooltip closeDelay={0} delay={250}>
                <Tooltip.Trigger>{chip}</Tooltip.Trigger>
                <Tooltip.Content
                  offset={8}
                  className="max-w-[min(360px,calc(100vw-32px))] rounded-xl border border-(--schemes-blue-100) bg-white px-3 py-2 text-xs font-medium leading-relaxed text-(--schemes-blue-900) shadow-[0_8px_24px_rgba(24,95,165,0.14)]"
                >
                  <Tooltip.Arrow className="fill-white text-(--schemes-blue-100)" />
                  <span className={cn(productCardHeading, "mb-1 block text-sm")}>
                    {suggestion.label}
                  </span>
                  <span className="block whitespace-normal break-normal">
                    {suggestion.value}
                  </span>
                </Tooltip.Content>
              </Tooltip>
            ) : (
              chip
            )}
          </motion.div>
        );
      })}
    </ScrollShadow>
  );
}
