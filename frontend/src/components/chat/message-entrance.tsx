"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { motionPreset, transition } from "@/lib/design-system/motion";

type MessageEntranceProps = {
  children: React.ReactNode;
  className?: string;
  "aria-live"?: React.AriaAttributes["aria-live"];
  role?: React.AriaRole;
};

export function MessageEntrance({
  children,
  className,
  "aria-live": ariaLive,
  role,
}: MessageEntranceProps) {
  return (
    <motion.div
      initial={motionPreset.fadeInUpXs.initial}
      animate={motionPreset.fadeInUpXs.animate}
      transition={transition.state}
      className={cn(className)}
      aria-live={ariaLive}
      role={role}
    >
      {children}
    </motion.div>
  );
}
