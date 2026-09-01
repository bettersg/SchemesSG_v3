"use client";

import { useEffect, useState } from "react";
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
 * Dense reference sidebar, in the Stripe API reference arrangement: a flat list
 * of every section pinned beside the content for the whole scroll, with the
 * current section marked.
 *
 * Sits below the site navbar rather than replacing it, so the docs surface stays
 * inside the site rather than becoming its own shell.
 *
 * Not built on `useSchemeSectionNavigation`, which does similar anchor tracking:
 * that hook needs a sticky-header ref and a measured offset and looks for an
 * `.overflow-y-auto` scroll container, all specific to the scheme detail page.
 */
export function DocsSidebar({
  heading,
  items,
}: {
  heading: string;
  items: NavItem[];
}) {
  const [activeId, setActiveId] = useState<string>(items[0]?.id ?? "");

  useEffect(() => {
    const sections = items
      .map((item) => document.getElementById(item.id))
      .filter((element): element is HTMLElement => element !== null);

    if (sections.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActiveId(visible[0].target.id);
      },
      // Bias the band to the top so the heading being read wins, not one below it.
      { rootMargin: "-92px 0px -70% 0px", threshold: 0 },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [items]);

  // pt-nav clears the fixed site navbar on mobile, where this strip is the first
  // thing in the flow. At lg the sticky top-nav offset already does that job.
  return (
    <nav
      aria-label={heading}
      className="min-w-0 border-(--schemes-border) px-4 pt-nav sm:px-8 lg:sticky lg:top-nav lg:h-[calc(100vh-var(--spacing-nav))] lg:overflow-y-auto lg:border-r lg:px-0 lg:pt-0 lg:py-8"
    >
      <h2 className="mb-2 hidden px-3 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase lg:block">
        {heading}
      </h2>
      {/* Full-bleed scroll strip on mobile: the negative margin must match the
          nav's own padding at every breakpoint, or it overflows the viewport. */}
      <ul className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-2 sm:-mx-8 sm:px-8 lg:mx-0 lg:flex-col lg:overflow-visible lg:px-2 lg:pb-0">
        {items.map((item) => {
          const isActive = activeId === item.id;
          return (
            <li key={item.id} className="shrink-0 lg:shrink">
              <a
                href={`#${item.id}`}
                aria-current={isActive ? "true" : undefined}
                className={cn(
                  "flex min-h-11 items-center gap-2 rounded-md px-3 text-[13px] transition-colors duration-150 ease-out lg:min-h-0 lg:py-1.5",
                  item.nested && "lg:pl-6",
                  isActive
                    ? "bg-(--schemes-blue-50) font-semibold text-(--schemes-blue-900)"
                    : "text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50)/60 hover:text-(--schemes-blue-600)",
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
          );
        })}
      </ul>
    </nav>
  );
}
