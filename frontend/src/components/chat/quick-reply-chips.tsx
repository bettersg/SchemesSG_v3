"use client";
import { Chip } from "@heroui/react";

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
    <div className="flex flex-col md:flex-row items-start gap-2 px-4 py-2 overflow-x-auto no-scrollbar shrink-0 flex-wrap">
      {suggestions.map((s) => (
        <Chip
          key={s.label}
          onClick={() => onSelect(s.value)}
          color="accent"
          variant="soft"
          className="shrink-0 cursor-pointer whitespace-nowrap hover:bg-[#E6F1FB] transition-all"
        >
          <Chip.Label>{s.label}</Chip.Label>
        </Chip>
      ))}
    </div>
  );
}
