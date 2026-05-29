import Link from "next/link";
import { Scheme } from "@/types/types";
import clsx from "clsx";
import SchemeLogo from "./scheme-logo";
import CategoryTag from "./category-tag";
import { productCard } from "@/lib/design-system/product-styles";
import { SCHEME_CATEGORIES } from "@/lib/design-system/categories";

interface SchemeCardProps {
  scheme: Scheme;
  className?: string;
}

function SchemeCard({ scheme, className }: SchemeCardProps) {
  // sort scheme types, putting any of the 10 scheme categories in the front
  // slice to the first 2 types
  const sortedTypes = [...scheme.schemeType].sort((a, b) => {
    return (
      Number(
        SCHEME_CATEGORIES.includes(b as (typeof SCHEME_CATEGORIES)[number]),
      ) -
      Number(
        SCHEME_CATEGORIES.includes(a as (typeof SCHEME_CATEGORIES)[number]),
      )
    );
  });
  console.log(sortedTypes);
  const types = sortedTypes.slice(0, 2);
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      target="_blank"
      rel="noopener noreferrer"
      className={clsx(
        productCard,
        "shrink-0 text-left p-4 hover:shadow-[0_4px_16px_rgba(24,95,165,0.08)] hover:-translate-y-0.5 transition-[box-shadow,transform] group relative overflow-hidden",
        className,
      )}
    >
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

export default SchemeCard;
