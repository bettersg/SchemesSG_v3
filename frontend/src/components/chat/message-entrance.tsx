"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type MessageEntranceProps = {
  children: React.ReactNode;
  className?: string;
};

export function MessageEntrance({ children, className }: MessageEntranceProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.16, ease: "easeOut" }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
