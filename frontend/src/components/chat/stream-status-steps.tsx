"use client";

import { WordRotate } from "@/components/animations/word-rotate";
import ChatSpinner from "@/components/chat/chat-spinner";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import {
  statusStepContainerClass,
  statusStepIndicatorClass,
  statusStepSummaryClass,
} from "@/components/chat/status-step-styles";

export type StatusStep = {
  id: string;
  label: string;
  phase?: string;
};

type StreamStatusStepsProps = {
  steps: StatusStep[];
  isActive?: boolean;
};

export function StreamStatusSteps({
  steps,
  isActive = false,
}: StreamStatusStepsProps) {
  const latestStep = steps.at(-1);

  if (!isActive || !latestStep) return null;

  return (
    <div className={statusStepContainerClass}>
      <div className={statusStepSummaryClass}>
        <span className={`${statusStepIndicatorClass} relative`}>
          <ChatSpinner className="absolute left-1/2 top-1/2 size-8 max-w-none -translate-x-1/2 -translate-y-1/2" />
        </span>
        <WordRotate
          words={[latestStep.label]}
          className="min-w-0"
          renderWord={(label) => (
            <StatusTextShimmer className="block max-w-full truncate font-semibold">
              {label}
            </StatusTextShimmer>
          )}
        />
      </div>
    </div>
  );
}
