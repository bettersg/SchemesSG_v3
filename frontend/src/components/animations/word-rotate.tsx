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
  duration?: number;
  motionProps?: MotionProps;
  className?: string;
  renderWord?: (word: string) => ReactNode;
}

export function WordRotate({
  words,
  duration = 2500,
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

  useEffect(() => {
    if (shouldReduceMotion || words.length < 2) return;

    const interval = window.setInterval(() => {
      setIndex((previousIndex) => (previousIndex + 1) % words.length);
    }, duration);

    return () => window.clearInterval(interval);
  }, [words, duration, shouldReduceMotion]);

  const word = words[shouldReduceMotion ? 0 : index];

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
