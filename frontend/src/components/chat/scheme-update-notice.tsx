"use client";

import { motion } from "framer-motion";
import { motionPreset, transition } from "@/lib/design-system/motion";
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
      initial={motionPreset.fadeInUpXs.initial}
      animate={motionPreset.fadeInUpXs.animate}
      exit={motionPreset.fadeOutUpXs.exit}
      transition={transition.state}
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
