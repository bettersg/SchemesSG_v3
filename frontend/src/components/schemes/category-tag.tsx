import { getSchemeCategoryChipClassName } from "@/lib/design-system/categories";

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
  // Category names come from the scheme data, which is English, so the pill
  // keeps English pronunciation and is not enlarged by the Chinese and Tamil
  // size floors in globals.css.
  return (
    <span
      lang="en"
      className={getSchemeCategoryChipClassName(
        label,
        `${SIZE_CLASSES[size]} ${className ?? ""}`,
      )}
    >
      {label}
    </span>
  );
}
