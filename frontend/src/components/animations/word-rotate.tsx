"use client";

import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion, type MotionProps } from "framer-motion";

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

  useEffect(() => {
    if (words.length < 2) return;

    const interval = window.setInterval(() => {
      setIndex((previousIndex) => (previousIndex + 1) % words.length);
    }, duration);

    return () => window.clearInterval(interval);
  }, [words, duration]);

  const word = words[index];

  if (!word) return null;

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
