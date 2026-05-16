"use client";
import { Chip } from "@heroui/react";
import { productActionChip } from "@/lib/design-system/product-styles";

export type QuickReply = {
  label: string;
  value: string;
};

interface QuickReplyChipsProps {
  suggestions: QuickReply[];
  onSelect: (text: string) => void;
}

export default function QuickReplyChips({
  suggestions,
  onSelect,
}: QuickReplyChipsProps) {
  if (!suggestions.length) return null;
  return (
    <div className="flex flex-row flex-wrap items-start gap-2 px-4 py-2  no-scrollbar shrink-0">
      {suggestions.slice(0, 3).map((s) => (
        <Chip
          key={s.label}
          onClick={() => onSelect(s.value)}
          color="accent"
          variant="soft"
          className={`${productActionChip} shrink-0 cursor-pointer whitespace-nowrap`}
        >
          <Chip.Label>{s.label}</Chip.Label>
        </Chip>
      ))}
    </div>
  );
}
