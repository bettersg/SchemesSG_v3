"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { duration, ease } from "@/lib/design-system/motion";

type MessageEntranceProps = {
  children: React.ReactNode;
  className?: string;
};

export function MessageEntrance({ children, className }: MessageEntranceProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: duration.state, ease: ease.out }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
