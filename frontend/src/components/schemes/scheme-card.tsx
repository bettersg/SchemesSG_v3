import Link from "next/link";
import { Scheme } from "@/types/types";
import clsx from "clsx";
import SchemeLogo from "./scheme-logo";
import CategoryTag from "./category-tag";
import { productCard } from "@/lib/design-system/product-styles";
import { getSchemeCategory } from "@/lib/design-system/categories";

interface SchemeCardProps {
  scheme: Scheme;
  className?: string;
}

function SchemeCard({ scheme, className }: SchemeCardProps) {
  // sort scheme types, putting any of the 10 scheme categories in the front
  // slice to the first 2 types
  const hasCategory = (type: string) => getSchemeCategory(type) !== undefined;
  const sortedTypes = [...scheme.schemeType].sort((a, b) => {
    return Number(hasCategory(b)) - Number(hasCategory(a));
  });
  const types = sortedTypes.slice(0, 2);
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx(
        productCard,
        "group relative flex h-full min-h-[148px] w-full flex-col overflow-hidden p-4 text-left no-underline transition-[box-shadow,transform] hover:-translate-y-0.5 hover:shadow-[0_4px_16px_rgba(24,95,165,0.08)] hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
        className,
      )}
    >
      <div className="flex gap-2.5 items-start mb-2.5">
        <SchemeLogo agency={scheme.agency} image={scheme.image} />
        <div className="flex-1 min-w-0">
          <p className="text-[12.5px] font-semibold text-(--schemes-blue-900) leading-snug line-clamp-2">
            {scheme.schemeName}
          </p>
          <p className="text-xs text-(--schemes-muted) mt-0.5 line-clamp-2">
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

export default SchemeCard;
