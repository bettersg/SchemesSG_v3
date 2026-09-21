"use client";

import { useEffect, useState, type ReactNode } from "react";
import {
  AnimatePresence,
  motion,
  type MotionProps,
  useReducedMotion,
} from "framer-motion";

import { cn } from "@/lib/utils";

interface WordRotateProps {
  words: string[];
  /** Shortest dwell per word. Pass the same value as maxDuration for a fixed cadence. */
  minDuration: number;
  /** Longest dwell per word. Each step re-rolls inside [min, max]. */
  maxDuration: number;
  motionProps?: MotionProps;
  className?: string;
  renderWord?: (word: string) => ReactNode;
}

export function WordRotate({
  words,
  minDuration,
  maxDuration,
  motionProps = {
    initial: { opacity: 0, y: -8 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 8 },
    transition: { duration: 0.2, ease: "easeOut" },
  },
  className,
  renderWord,
}: WordRotateProps) {
  const [index, setIndex] = useState(0);
  const shouldReduceMotion = useReducedMotion();

  // Self-rescheduling rather than setInterval: a fixed cadence reads as a
  // machine ticking, so each step re-rolls its own dwell.
  useEffect(() => {
    if (shouldReduceMotion || words.length < 2) return;

    let timer: number;

    const scheduleNext = () => {
      const dwell = minDuration + Math.random() * (maxDuration - minDuration);
      timer = window.setTimeout(() => {
        setIndex((previousIndex) => (previousIndex + 1) % words.length);
        scheduleNext();
      }, dwell);
    };

    scheduleNext();

    return () => window.clearTimeout(timer);
  }, [words, minDuration, maxDuration, shouldReduceMotion]);

  // Clamped because `words` can shrink under a live index — a caller swapping a
  // long list for a shorter one mid-rotation would otherwise read past the end
  // and render nothing.
  const word =
    words[shouldReduceMotion ? 0 : Math.min(index, words.length - 1)];

  if (!word) return null;

  if (shouldReduceMotion) {
    return (
      <span className="block min-w-0 flex-1 overflow-hidden">
        <span className={cn("block min-w-0", className)}>
          {renderWord ? renderWord(word) : word}
        </span>
      </span>
    );
  }

  return (
    <span className="block min-w-0 flex-1 overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.span
          key={word}
          className={cn("block min-w-0", className)}
          {...motionProps}
        >
          {renderWord ? renderWord(word) : word}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
