"use client";

import { AnimatePresence, motion } from "framer-motion";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";

export type StreamStatusStep = {
  id: string;
  label: string;
  phase?: string;
};

type StreamStatusStepsProps = {
  steps: StreamStatusStep[];
  isActive?: boolean;
};

export function StreamStatusSteps({
  steps,
  isActive = false,
}: StreamStatusStepsProps) {
  if (!steps.length) return null;

  // const visibleSteps = steps.slice(-3);

  return (
    <div className="mt-2 flex flex-col gap-1.5">
      <AnimatePresence initial={false}>
        {steps.map((step, index) => {
          const isLatest = index === steps.length - 1;
          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: isLatest ? 1 : 0.72, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.16, ease: "easeOut" }}
              className="flex items-center gap-2 text-xs text-(--schemes-status-info-text)"
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isActive && isLatest
                    ? "animate-pulse bg-(--schemes-blue-400)"
                    : "bg-(--schemes-status-info-border)"
                }`}
              />
              {isActive && isLatest ? (
                <StatusTextShimmer className="font-semibold">
                  {step.label}
                </StatusTextShimmer>
              ) : (
                <span>{step.label}</span>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
