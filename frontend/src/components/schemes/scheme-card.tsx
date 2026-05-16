import Link from "next/link";
import { Scheme } from "@/types/types";
import { Chip } from "@heroui/react";
import clsx from "clsx";
import SchemeLogo from "./scheme-logo";
import {
  getSchemeCategoryChipClassName,
  normalizeSchemeCategory,
} from "@/lib/design-system/categories";
import { productCard } from "@/lib/design-system/product-styles";

interface SchemeCardProps {
  scheme: Scheme;
  className?: string;
}

function SchemeCard({ scheme, className }: SchemeCardProps) {
  const types = scheme.schemeType.slice(0, 2);
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx(
        productCard,
        "shrink-0 text-left p-4 hover:border-(--schemes-blue-100) hover:shadow-[0_2px_12px_rgba(24,95,165,0.1)] hover:-translate-y-0.5 transition-[border-color,box-shadow,transform] group relative overflow-hidden",
        className,
      )}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-(--schemes-blue-400) opacity-0 group-hover:opacity-100 transition-opacity rounded-l-xl" />
      <div className="flex gap-2.5 items-start mb-2.5">
        <SchemeLogo agency={scheme.agency} image={scheme.image} />
        <div className="flex-1 min-w-0">
          <p className="text-[12.5px] font-semibold text-(--schemes-blue-900) leading-snug line-clamp-2">
            {scheme.schemeName}
          </p>
          <p className="text-xs text-(--schemes-muted) mt-0.5">
            {scheme.agency}
          </p>
        </div>
      </div>
      <div className="flex gap-1 flex-wrap mb-2">
        {types.map((t) => (
          <CategoryTag key={t} label={t} />
        ))}
      </div>
      <p className="text-xs text-(--schemes-muted) leading-relaxed line-clamp-2">
        {scheme.summary || scheme.description}
      </p>
    </Link>
  );
}

function CategoryTag({ label }: { label: string }) {
  const normalizedLabel = normalizeSchemeCategory(label);
  return (
    <Chip
      className={getSchemeCategoryChipClassName(
        label,
        "text-[10px] px-2 py-0.5 font-semibold",
      )}
      size="sm"
    >
      {normalizedLabel}
    </Chip>
  );
}

export default SchemeCard;
