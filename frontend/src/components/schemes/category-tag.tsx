import {
  getSchemeCategoryChipClassName,
  normalizeSchemeCategory,
} from "@/lib/design-system/categories";

type Size = "sm" | "md";

interface CategoryTagProps {
  label: string;
  size?: Size;
  className?: string;
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: "text-[10px] px-2 py-0.5 font-semibold",
  md: "text-[11px] px-2.5 py-0.5 font-semibold",
};

export default function CategoryTag({
  label,
  size = "sm",
  className,
}: CategoryTagProps) {
  return (
    <span className={getSchemeCategoryChipClassName(label, `${SIZE_CLASSES[size]} ${className ?? ""}`)}>
      {normalizeSchemeCategory(label)}
    </span>
  );
}
