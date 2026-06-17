"use client";

import { Button, Drawer, useOverlayState } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import { Check, ChevronDown } from "lucide-react";
import clsx from "clsx";
import {
  CATALOG_CATEGORY_ICON_SRC,
  CATALOG_CATEGORY_OPTIONS,
  CATALOG_CATEGORY_SLUGS,
  type CatalogCategory,
} from "@/lib/design-system/categories";

type CatalogCategoryDrawerProps = {
  activeCategory: CatalogCategory;
  className?: string;
};

// Mobile-only (<md) collapsed presentation of the catalog category chips: a
// trigger pill showing the active category that opens a bottom-sheet picker.
// Single-select — each row is a Link to that category's static route, so the
// existing server-side fetch + per-category SEO are preserved; the drawer is
// purely a different shape over the same navigation the desktop chips do.
function CatalogCategoryDrawer({
  activeCategory,
  className,
}: CatalogCategoryDrawerProps) {
  const drawerState = useOverlayState();
  const activeLabel = activeCategory === "All" ? "All Schemes" : activeCategory;

  return (
    <Drawer state={drawerState}>
      <Button
        aria-label="Filter by category"
        className={clsx(
          "inline-flex min-h-11 flex-1 items-center gap-2 rounded-full border border-(--schemes-border-neutral) bg-white px-4 py-2 text-sm font-semibold text-(--schemes-ink-soft) transition-[background-color,border-color,color] hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
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
        <span className="min-w-0 flex-1 truncate text-left">{activeLabel}</span>
        <ChevronDown size={14} strokeWidth={2} className="shrink-0 opacity-70" />
      </Button>
      {/* Mirror the schemes-filter bottom-sheet chrome: a transparent overlay
          hosting the surface sheet, so the dim scrim signals the page is still
          there. */}
      <Drawer.Backdrop className="bg-black/50">
        <Drawer.Content placement="bottom" className="bg-transparent">
          <Drawer.Dialog className="flex max-h-[80vh] flex-col rounded-t-2xl bg-(--schemes-surface) pt-3 outline-none">
            <Drawer.Handle />
            <h2 className="shrink-0 px-4 pb-2 pt-1 font-(--font-head) text-lg font-semibold text-(--schemes-blue-900)">
              Categories
            </h2>
            <div className="thin-scrollbar min-h-0 flex-1 overflow-y-auto p-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))]">
              {CATALOG_CATEGORY_OPTIONS.map((cat) => {
                const isActive = cat === activeCategory;
                return (
                  <Link
                    key={cat}
                    href={`/catalog/${CATALOG_CATEGORY_SLUGS[cat]}`}
                    onClick={() => drawerState.close()}
                    aria-current={isActive ? "page" : undefined}
                    className={clsx(
                      "flex min-h-12 w-full items-center gap-3 rounded-lg px-3 text-base no-underline transition-colors",
                      isActive
                        ? "bg-(--schemes-blue-50) text-(--schemes-blue-600)"
                        : "text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50)",
                    )}
                  >
                    <Image
                      src={CATALOG_CATEGORY_ICON_SRC[cat]}
                      alt=""
                      width={24}
                      height={24}
                      aria-hidden="true"
                      className="size-6 shrink-0"
                    />
                    <span className="min-w-0 flex-1 truncate">
                      {cat === "All" ? "All Schemes" : cat}
                    </span>
                    {isActive && (
                      <Check
                        size={18}
                        strokeWidth={2.5}
                        className="shrink-0 text-(--schemes-blue-600)"
                      />
                    )}
                  </Link>
                );
              })}
            </div>
          </Drawer.Dialog>
        </Drawer.Content>
      </Drawer.Backdrop>
    </Drawer>
  );
}

export default CatalogCategoryDrawer;
