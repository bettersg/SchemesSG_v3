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
  // One wayfinding chip: the top category carries "what kind of help this is"
  // without turning a dense grid into a field of coloured pills.
  const topType = sortedTypes[0];
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${scheme.schemeName}, ${scheme.agency} (opens in new tab)`}
      className={clsx(
        productCard,
        "group relative flex h-full min-h-[148px] w-full flex-col overflow-hidden p-4 text-left no-underline transition-[box-shadow,transform] hover:-translate-y-0.5 hover:bg-(--schemes-blue-50) hover:shadow-[0_2px_12px_rgba(24,95,165,0.1)] hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-400)",
        className,
      )}
    >
      <div className="mb-3 flex items-start gap-3">
        <SchemeLogo agency={scheme.agency} image={scheme.image} />
        <div className="min-w-0 flex-1">
          <h3
            title={scheme.schemeName}
            className="font-(--font-head) text-[0.95rem] font-semibold leading-snug text-(--schemes-blue-900) line-clamp-2"
          >
            {scheme.schemeName}
          </h3>
          <p
            title={scheme.agency}
            className="mt-1 truncate text-xs text-(--schemes-muted)"
          >
            {scheme.agency}
          </p>
        </div>
      </div>
      <p className="line-clamp-2 text-xs leading-relaxed text-(--schemes-ink-soft)">
        {scheme.summary || scheme.description}
      </p>
      {topType && (
        <div className="mt-auto flex flex-wrap gap-1 pt-3">
          <CategoryTag label={topType} />
        </div>
      )}
    </Link>
  );
}

export default SchemeCard;
