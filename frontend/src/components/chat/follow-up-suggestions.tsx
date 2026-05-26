"use client";

import { motion } from "framer-motion";
import {
  productButtonSecondary,
  productButtonSm,
} from "@/lib/design-system/product-styles";

export type FollowUpSuggestion = {
  label: string;
  value: string;
};

type FollowUpSuggestionsProps = {
  suggestions: FollowUpSuggestion[];
  onSelect: (value: string) => void;
};

export function FollowUpSuggestions({
  suggestions,
  onSelect,
}: FollowUpSuggestionsProps) {
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-row flex-wrap items-start gap-2 px-4 py-2 no-scrollbar shrink-0">
      {suggestions.slice(0, 3).map((suggestion, index) => (
        <motion.div
          key={suggestion.label}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.045, duration: 0.16 }}
        >
          <button
            type="button"
            onClick={() => onSelect(suggestion.value)}
            className={`${productButtonSecondary} ${productButtonSm} shrink-0 cursor-pointer whitespace-nowrap rounded-full`}
          >
            {suggestion.label}
          </button>
        </motion.div>
      ))}
    </div>
  );
}
