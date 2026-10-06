"use client";

import { Button, Drawer, Popover, useOverlayState } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import { Check, ChevronDown } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import { useIsDesktop } from "@/hooks/use-is-desktop";
import {
  CATALOG_CATEGORY_ICON_SRC,
  CATALOG_CATEGORY_OPTIONS,
  type CatalogCategory,
} from "@/lib/design-system/categories";
import { getCatalogCategoryPath } from "@/lib/catalog-seo";

type CatalogCategorySelectProps = {
  activeCategory: CatalogCategory;
  className?: string;
};

const categoryLabel = (cat: CatalogCategory) =>
  cat === "All" ? "All Schemes" : cat;

// Single-select list of every catalog category. Each row is a Link to that
// category's static route, so per-category prerendering and SEO are untouched;
// this is only a different shape over the same navigation.
function CategoryList({
  activeCategory,
  onNavigate,
  size,
}: {
  activeCategory: CatalogCategory;
  onNavigate: () => void;
  size: "sm" | "lg";
}) {
  const lg = size === "lg";

  return (
    <div
      className={clsx(
        "thin-scrollbar min-h-0 flex-1 overflow-y-auto",
        lg ? "p-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))]" : "p-1",
      )}
    >
      {CATALOG_CATEGORY_OPTIONS.map((cat) => {
        const isActive = cat === activeCategory;
        return (
          <Link
            key={cat}
            href={getCatalogCategoryPath(cat)}
            onClick={onNavigate}
            aria-current={isActive ? "page" : undefined}
            className={clsx(
              "flex w-full items-center rounded-lg no-underline transition-colors",
              lg
                ? "min-h-12 gap-3 px-3 text-base"
                : "min-h-9 gap-2.5 px-2 text-sm",
              isActive
                ? "bg-(--schemes-blue-50) font-semibold text-(--schemes-blue-600)"
                : "text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50)",
            )}
          >
            <Image
              src={CATALOG_CATEGORY_ICON_SRC[cat]}
              alt=""
              width={lg ? 24 : 20}
              height={lg ? 24 : 20}
              aria-hidden="true"
              className={clsx("shrink-0", lg ? "size-6" : "size-5")}
            />
            <span className="min-w-0 flex-1 truncate">
              {categoryLabel(cat)}
            </span>
            {isActive && (
              <Check
                size={lg ? 18 : 15}
                strokeWidth={2.5}
                className="shrink-0 text-(--schemes-blue-600)"
              />
            )}
          </Link>
        );
      })}
    </div>
  );
}

// Category picker for the catalog results header. Mirrors the schemes-filter
// affordance: a popover on desktop, a bottom-sheet drawer on mobile where
// popover rows are too small to tap reliably.
function CatalogCategorySelect({
  activeCategory,
  className,
}: CatalogCategorySelectProps) {
  const isDesktop = useIsDesktop();
  const drawerState = useOverlayState();
  // Popover is a React Aria DialogTrigger, so it is controlled by isOpen rather
  // than the overlay state object Drawer takes.
  const [popoverOpen, setPopoverOpen] = useState(false);

  const trigger = (
    <Button
      aria-label="Browse by category"
      className={clsx(
        "inline-flex min-h-11 items-center gap-2 rounded-full border border-(--schemes-border-neutral) bg-white px-4 py-2 text-sm font-semibold text-(--schemes-ink-soft) transition-[background-color,border-color,color] hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
        className,
      )}
    >
      <Image
        src={CATALOG_CATEGORY_ICON_SRC[activeCategory]}
        alt=""
        width={20}
        height={20}
        aria-hidden="true"
        className="size-5 shrink-0"
      />
      <span className="min-w-0 flex-1 truncate text-left">
        {categoryLabel(activeCategory)}
      </span>
      <ChevronDown size={14} strokeWidth={2} className="shrink-0 opacity-70" />
    </Button>
  );

  if (isDesktop) {
    return (
      <Popover isOpen={popoverOpen} onOpenChange={setPopoverOpen}>
        {trigger}
        {/* Anchored to the trigger's end edge: the control sits at the right of
            the results header, so a start-anchored panel would overflow. */}
        <Popover.Content
          placement="bottom end"
          className="z-50 w-[min(80vw,260px)] rounded-xl border border-(--schemes-border) bg-(--schemes-surface) p-0 shadow-sm"
        >
          <Popover.Dialog className="m-0 flex max-h-[min(60vh,420px)] flex-col p-0 outline-none">
            <CategoryList
              activeCategory={activeCategory}
              onNavigate={() => setPopoverOpen(false)}
              size="sm"
            />
          </Popover.Dialog>
        </Popover.Content>
      </Popover>
    );
  }

  return (
    <Drawer state={drawerState}>
      {trigger}
      <Drawer.Backdrop className="bg-black/50">
        <Drawer.Content placement="bottom" className="bg-transparent">
          <Drawer.Dialog className="flex max-h-[80vh] flex-col rounded-t-2xl bg-(--schemes-surface) pt-3 outline-none">
            <Drawer.Handle />
            <h2 className="shrink-0 px-4 pb-2 pt-1 font-(--font-head) text-lg font-semibold text-(--schemes-blue-900)">
              Categories
            </h2>
            <CategoryList
              activeCategory={activeCategory}
              onNavigate={() => drawerState.close()}
              size="lg"
            />
          </Drawer.Dialog>
        </Drawer.Content>
      </Drawer.Backdrop>
    </Drawer>
  );
}

export default CatalogCategorySelect;
