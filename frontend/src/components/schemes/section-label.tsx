import { ReactNode } from "react";

interface SectionLabelProps {
  children: ReactNode;
  accent?: string;
}

export default function SectionLabel({
  children,
  accent = "bg-(--schemes-blue-400)",
}: SectionLabelProps) {
  return (
    <div className="mb-3 flex items-center gap-2.5">
      <span className={`h-2 w-2 rounded-[3px] ${accent}`} aria-hidden="true" />
      <h3 className="text-sm font-semibold text-(--schemes-blue-900)">
        {children}
      </h3>
    </div>
  );
}
