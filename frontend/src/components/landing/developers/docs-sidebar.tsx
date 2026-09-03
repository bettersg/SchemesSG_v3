import type { HttpMethod } from "@/lib/partner-api-reference";
import { cn } from "@/lib/utils";
import { MethodBadge } from "./api-primitives";

export type NavItem = {
  id: string;
  label: string;
  method?: HttpMethod;
  nested?: boolean;
};

/**
 * Dense reference sidebar: a flat list of every section, pinned beside the
 * content for the whole scroll.
 *
 * Sits below the site navbar rather than replacing it, so the docs surface stays
 * inside the site rather than becoming its own shell.
 *
 * ponytail: no scroll-spy. Plain anchors already navigate, the sections already
 * carry `scroll-mt-24`, and skipping the IntersectionObserver keeps this a server
 * component — so the sidebar ships no JavaScript at all. Add an active marker if
 * readers actually report losing their place.
 */
export function DocsSidebar({
  heading,
  items,
}: {
  heading: string;
  items: NavItem[];
}) {
  // pt-nav clears the fixed site navbar on mobile, where this strip is the first
  // thing in the flow. At lg the sticky top-nav offset already does that job.
  return (
    <nav
      aria-label={heading}
      className="thin-scrollbar min-w-0 border-(--schemes-border) px-4 pt-nav sm:px-8 lg:sticky lg:top-nav lg:h-[calc(100vh-var(--spacing-nav))] lg:overflow-y-auto lg:border-r lg:px-0 lg:pt-0 lg:py-8"
    >
      <h2 className="mb-2 hidden px-3 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase lg:block">
        {heading}
      </h2>
      {/* Full-bleed scroll strip on mobile: the negative margin must match the
          nav's own padding at every breakpoint, or it overflows the viewport. */}
      {/* no-scrollbar on the mobile strip, matching every other horizontal chip
          row in the app (features-section, follow-up-suggestions, catalog-detail):
          the row is short and obviously swipeable, so a chunky bar is noise. */}
      <ul className="no-scrollbar -mx-4 flex gap-1 overflow-x-auto px-4 pb-2 sm:-mx-8 sm:px-8 lg:mx-0 lg:flex-col lg:overflow-visible lg:px-2 lg:pb-0">
        {items.map((item) => (
          <li key={item.id} className="shrink-0 lg:shrink">
            <a
              href={`#${item.id}`}
              className={cn(
                "flex min-h-11 items-center gap-2 rounded-md px-3 text-[13px] text-(--schemes-ink-soft) transition-colors duration-150 ease-out hover:bg-(--schemes-blue-50)/60 hover:text-(--schemes-blue-600) lg:min-h-0 lg:py-1.5",
                item.nested && "lg:pl-6",
              )}
            >
              <span className="whitespace-nowrap lg:whitespace-normal">
                {item.label}
              </span>
              {item.method ? (
                <MethodBadge
                  method={item.method}
                  className="ml-auto hidden lg:inline-flex"
                />
              ) : null}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
