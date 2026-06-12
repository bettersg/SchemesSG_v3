"use client";

import { motion } from "framer-motion";
import { duration, ease } from "@/lib/design-system/motion";

type SchemeUpdateNoticeProps = {
  count: number;
};

export function SchemeUpdateNotice({ count }: SchemeUpdateNoticeProps) {
  if (count <= 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: duration.state, ease: ease.out }}
      className="inline-flex w-fit items-center gap-2 rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) px-3 py-1.5 text-xs font-semibold text-(--schemes-status-info-text)"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-(--schemes-blue-400)" />
      {count} {count === 1 ? "scheme" : "schemes"} found
    </motion.div>
  );
}
