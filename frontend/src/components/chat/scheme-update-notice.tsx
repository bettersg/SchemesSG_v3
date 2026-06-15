"use client";

import { motion } from "framer-motion";
import { duration, ease } from "@/lib/design-system/motion";
import { Button } from "../landing/ui/button";
import { PressEvent } from "@heroui/react";
import { clsx } from "clsx";
import { productButtonOutlineBlue } from "@/lib/design-system/product-styles";

type SchemeUpdateNoticeProps = {
  count: number;
  onNoticePress: (e: PressEvent) => void;
};

export function SchemeUpdateNotice({
  count,
  onNoticePress,
}: SchemeUpdateNoticeProps) {
  if (count <= 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: duration.state, ease: ease.out }}
    >
      <Button
        className={clsx(
          "inline-flex w-fit items-center gap-2",
          productButtonOutlineBlue,
          "text-xs font-semibold text-(--schemes-status-info-text)",
        )}
        onPress={onNoticePress}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-(--schemes-blue-400)" />
        {count} {count === 1 ? "scheme" : "schemes"} found
      </Button>
    </motion.div>
  );
}
