"use client";

import { Button, ScrollShadow, Tooltip } from "@heroui/react";
import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  productButtonCompact,
  productButtonOutlineBlue,
  productCardHeading,
} from "@/lib/design-system/product-styles";
import {
  delay,
  motionPreset,
  stagger,
  timeout,
  transition,
} from "@/lib/design-system/motion";
import { cn } from "@/lib/utils";

export type FollowUpSuggestion = {
  label: string;
  value: string;
};

type FollowUpSuggestionsProps = {
  suggestions: FollowUpSuggestion[];
  onSelect: (value: string) => void;
};

function FollowUpTooltipContent({
  suggestion,
}: {
  suggestion: FollowUpSuggestion;
}) {
  return (
    <>
      <span className={cn(productCardHeading, "mb-1 block text-sm")}>
        {suggestion.label}
      </span>
      <span className="block whitespace-normal break-normal">
        {suggestion.value}
      </span>
    </>
  );
}

export function FollowUpSuggestions({
  suggestions,
  onSelect,
}: FollowUpSuggestionsProps) {
  // Desktop gets standard hover tooltips. Touch/coarse-pointer devices get an
  // explicit hold preview that disappears as soon as the press is released.
  const [hoverCapable, setHoverCapable] = useState(false);
  const [holdCapable, setHoldCapable] = useState(false);
  const [openHoldTooltipId, setOpenHoldTooltipId] = useState<string | null>(
    null,
  );
  const holdTimerRef = useRef<number | null>(null);
  const didRevealHoldTooltipRef = useRef(false);
  const controlledHoldTooltip = holdCapable && !hoverCapable;

  useEffect(() => {
    const hoverQuery = window.matchMedia(
      "(any-hover: hover) and (any-pointer: fine)",
    );
    const holdQuery = window.matchMedia(
      "(any-hover: none), (any-pointer: coarse)",
    );
    const update = () => {
      setHoverCapable(hoverQuery.matches);
      setHoldCapable(holdQuery.matches);
    };
    update();
    hoverQuery.addEventListener("change", update);
    holdQuery.addEventListener("change", update);
    return () => {
      hoverQuery.removeEventListener("change", update);
      holdQuery.removeEventListener("change", update);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (holdTimerRef.current !== null) {
        window.clearTimeout(holdTimerRef.current);
      }
    };
  }, []);

  if (!suggestions.length) return null;

  const clearHoldTimer = () => {
    if (holdTimerRef.current !== null) {
      window.clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  };

  const hideHoldTooltip = () => {
    clearHoldTimer();
    setOpenHoldTooltipId(null);
  };

  const showHoldTooltip = (id: string) => {
    if (!controlledHoldTooltip) return;
    clearHoldTimer();
    didRevealHoldTooltipRef.current = false;

    holdTimerRef.current = window.setTimeout(() => {
      didRevealHoldTooltipRef.current = true;
      setOpenHoldTooltipId(id);
    }, timeout.followUpHoldMs);
  };

  return (
    <ScrollShadow
      orientation="horizontal"
      className="no-scrollbar flex shrink-0 flex-row flex-nowrap gap-2 overflow-x-auto overflow-y-hidden px-4 py-2 sm:flex-wrap sm:overflow-visible sm:px-5"
    >
      {suggestions.map((suggestion, index) => {
        const id = `${suggestion.label}-${index}`;
        const chip = (
          <Button
            variant="outline"
            aria-label={`${suggestion.label}: ${suggestion.value}`}
            onPress={() => {
              if (didRevealHoldTooltipRef.current) {
                didRevealHoldTooltipRef.current = false;
                return;
              }
              onSelect(suggestion.value);
            }}
            onPointerDown={(event) => {
              if (event.pointerType === "mouse") return;
              showHoldTooltip(id);
            }}
            onPointerUp={hideHoldTooltip}
            onPointerCancel={hideHoldTooltip}
            onPointerLeave={hideHoldTooltip}
            onContextMenu={(event) => {
              if (controlledHoldTooltip) event.preventDefault();
            }}
            className={`${productButtonOutlineBlue} ${productButtonCompact} shrink-0 cursor-pointer touch-manipulation whitespace-nowrap rounded-full`}
          >
            {suggestion.label}
          </Button>
        );

        return (
          <motion.div
            key={suggestion.label}
            className="shrink-0"
            initial={motionPreset.fadeInUpXs.initial}
            animate={motionPreset.fadeInUpXs.animate}
            transition={{ ...transition.state, delay: index * stagger }}
          >
            <Tooltip
              closeDelay={0}
              delay={
                controlledHoldTooltip ? delay.none : delay.tooltipPreviewMs
              }
              isDisabled={!hoverCapable && !controlledHoldTooltip}
              isOpen={
                controlledHoldTooltip ? openHoldTooltipId === id : undefined
              }
            >
              <Tooltip.Trigger>{chip}</Tooltip.Trigger>
              <Tooltip.Content
                offset={8}
                className="max-w-[min(360px,calc(100vw-32px))] rounded-xl border border-(--schemes-blue-100) bg-white px-3 py-2 text-xs font-medium leading-relaxed text-(--schemes-blue-900) shadow-[0_8px_24px_rgba(24,95,165,0.14)]"
              >
                <Tooltip.Arrow className="fill-white text-(--schemes-blue-100)" />
                <FollowUpTooltipContent suggestion={suggestion} />
              </Tooltip.Content>
            </Tooltip>
          </motion.div>
        );
      })}
    </ScrollShadow>
  );
}
