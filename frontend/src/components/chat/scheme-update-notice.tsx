"use client";

import { motion } from "framer-motion";
import { duration, ease } from "@/lib/design-system/motion";
import { Button } from "../landing/ui/button";
import { PressEvent } from "@heroui/react";
import { clsx } from "clsx";
import { productButtonOutlineBlue } from "@/lib/design-system/product-styles";

type SchemeUpdateNoticeProps = {
  count: number;
  // When provided (mobile), the notice is a button that jumps to the Schemes
  // tab. On desktop the schemes list is always visible, so it renders as a
  // static badge instead.
  onNoticePress?: (e: PressEvent) => void;
};

export function SchemeUpdateNotice({
  count,
  onNoticePress,
}: SchemeUpdateNoticeProps) {
  if (count <= 0) return null;

  const label = (
    <>
      <span className="h-1.5 w-1.5 rounded-full bg-(--schemes-blue-400)" />
      {count} {count === 1 ? "scheme" : "schemes"} found
    </>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: duration.state, ease: ease.out }}
    >
      {onNoticePress ? (
        <Button
          className={clsx(
            "inline-flex w-fit items-center gap-2",
            productButtonOutlineBlue,
            "text-xs font-semibold text-(--schemes-status-info-text)",
          )}
          onPress={onNoticePress}
        >
          {label}
        </Button>
      ) : (
        <span
          className={clsx(
            "inline-flex w-fit items-center gap-2",
            productButtonOutlineBlue,
            "text-xs font-semibold text-(--schemes-status-info-text)",
          )}
        >
          {label}
        </span>
      )}
    </motion.div>
  );
}
