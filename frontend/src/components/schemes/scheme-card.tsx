import Link from "next/link";
import { Scheme } from "@/types/types";
import clsx from "clsx";
import SchemeLogo from "./scheme-logo";
import CategoryTag from "./category-tag";
import { productCard } from "@/lib/design-system/product-styles";
import { getSchemeCategory } from "@/lib/design-system/categories";
import { track } from "@/lib/analytics";

interface SchemeCardProps {
  scheme: Scheme;
  className?: string;
  headingLevel?: 2 | 3;
  /**
   * Which list this card sits in, and where. Supplied by the parent because the
   * card cannot know: the same card renders in the catalog grid and in the chat
   * results panel, and comparing the two is the point of recording it. Omit to
   * render the card without tracking the open.
   */
  list?: { id: string; index: number };
}

function SchemeCard({
  scheme,
  className,
  headingLevel = 3,
  list,
}: SchemeCardProps) {
  // sort scheme types, putting any of the 10 scheme categories in the front
  // slice to the first 2 types
  const hasCategory = (type: string) => getSchemeCategory(type) !== undefined;
  const sortedTypes = [...scheme.schemeType].sort((a, b) => {
    return Number(hasCategory(b)) - Number(hasCategory(a));
  });
  // One wayfinding chip: the top category carries "what kind of help this is"
  // without turning a dense grid into a field of coloured pills.
  const topType = sortedTypes[0];
  const Heading = headingLevel === 2 ? "h2" : "h3";
  return (
    <Link
      href={`/schemes/${scheme.schemeId}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${scheme.schemeName}, ${scheme.agency} (opens in new tab)`}
      onClick={
        list
          ? () =>
              track("select_item", {
                item_list_id: list.id,
                index: list.index,
                items: [
                  {
                    item_id: scheme.schemeId,
                    item_name: scheme.schemeName,
                    item_category: topType,
                  },
                ],
              })
          : undefined
      }
      className={clsx(
        productCard,
        "group relative flex h-full min-h-[148px] w-full flex-col overflow-hidden p-4 text-left no-underline transition-[box-shadow,transform] hover:-translate-y-0.5 hover:bg-(--schemes-blue-50) hover:shadow-[0_2px_12px_rgba(24,95,165,0.1)] hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-400)",
        className,
      )}
    >
      {/* Name, agency and the chip share one column so the logo has three rows
          to sit against. Most agency logos are a wordmark, which needs the
          resulting 64px tile to be legible at all. */}
      <div className="flex items-start gap-3">
        <SchemeLogo agency={scheme.agency} image={scheme.image} />
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <Heading
            title={scheme.schemeName}
            className="font-(--font-head) text-[0.95rem] font-semibold leading-snug text-(--schemes-blue-900) line-clamp-2"
          >
            {scheme.schemeName}
          </Heading>
          <p
            title={scheme.agency}
            className="truncate text-xs text-(--schemes-muted)"
          >
            {scheme.agency}
          </p>
          {/* self-start: the chip is inline-flex, which a flex column would
              otherwise stretch to the full text width. */}
          {topType && <CategoryTag label={topType} className="self-start" />}
        </div>
      </div>
      <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-(--schemes-ink-soft)">
        {scheme.summary || scheme.description}
      </p>
    </Link>
  );
}

export default SchemeCard;
