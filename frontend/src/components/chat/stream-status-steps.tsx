"use client";

import { useState } from "react";
import { WordRotate } from "@/components/animations/word-rotate";
import ChatSpinner from "@/components/chat/chat-spinner";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import {
  statusStepContainerClass,
  statusStepIndicatorClass,
  statusStepSummaryClass,
} from "@/components/chat/status-step-styles";
import { thinkingPhraseOrder } from "@/components/chat/thinking-phrases";
import { StatusStep } from "@/providers/chat-provider";

type StreamStatusStepsProps = {
  steps: StatusStep[];
  isActive?: boolean;
};

// Dwell bounds for the placeholder rotation. Averages near the 2500ms the row
// used to tick at, so its rhythm is unchanged.
const PHRASE_MIN_DWELL_MS = 1800;
const PHRASE_MAX_DWELL_MS = 3200;

export function StreamStatusSteps({
  steps,
  isActive = false,
}: StreamStatusStepsProps) {
  // Lazy initializer, so the shuffle happens once per mount rather than on
  // every render — a re-rolled array identity would reset the rotation timer
  // before it could ever fire. Also keeps Math.random() out of the render body,
  // where it would mismatch between server and client markup.
  const [phrases] = useState(() => thinkingPhraseOrder());
  const latestStep = steps.at(-1);

  // Deliberately not gated on having a step: the whole point is to fill the
  // window before the agent's first status event arrives over the network.
  if (!isActive) return null;

  const words = latestStep ? [latestStep.label] : phrases;

  return (
    <div className={statusStepContainerClass}>
      {/* One stable live region instead of announcing the visible text. The
          placeholder copy rotates every ~2s, and piping 20 decorative phrases
          through a screen reader is worse than saying nothing; real step labels
          are meaningful and change rarely, so those are announced as they come. */}
      {/* aria-live + aria-atomic rather than role="status", which is only sugar
          for the same pair: the schemes panel already owns a role="status", and a
          second one makes every bare getByRole("status") in the suite ambiguous. */}
      <span className="sr-only" aria-live="polite" aria-atomic="true">
        {latestStep ? latestStep.label : "Working on your answer"}
      </span>
      <div className={statusStepSummaryClass} aria-hidden="true">
        <span className={`${statusStepIndicatorClass} relative`}>
          <ChatSpinner className="absolute -left-2 top-1/2 size-8 max-w-none -translate-x-2 -translate-y-1/2" />
        </span>
        <WordRotate
          words={words}
          minDuration={PHRASE_MIN_DWELL_MS}
          maxDuration={PHRASE_MAX_DWELL_MS}
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
