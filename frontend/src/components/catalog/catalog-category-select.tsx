"use client";

import { Button, Drawer, Popover, useOverlayState } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import { Check, ChevronDown, MapPin } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import { useIsDesktop } from "@/hooks/use-is-desktop";
import { Trans, useLingui } from "@lingui/react/macro";
import {
  CATALOG_CATEGORY_ICON_SRC,
  CATALOG_CATEGORY_OPTIONS,
  type CatalogCategory,
  type SchemeCategory,
} from "@/lib/design-system/categories";
import { CATEGORY_LABELS } from "@/lib/design-system/category-labels";
import { planningAreaLabel } from "@/lib/planning-area-labels";
import {
  PLANNING_AREAS,
  getCatalogFilterHref,
  toggleValue,
} from "@/lib/catalog-filters";

type CatalogFilterKind = "category" | "area";

type CatalogCategorySelectProps = {
  /** Which list this control picks from. */
  kind?: CatalogFilterKind;
  /** Every selected category, the route's first; empty means all. */
  selectedCategories: SchemeCategory[];
  selectedAreas: string[];
  className?: string;
};

function useCategoryLabel() {
  const { t, i18n } = useLingui();
  return (cat: CatalogCategory) =>
    cat === "All" ? t`All Schemes` : i18n._(CATEGORY_LABELS[cat]);
}

function OptionRow({
  href,
  label,
  isSelected,
  icon,
  onNavigate,
  lg,
}: {
  href: string;
  label: string;
  isSelected: boolean;
  icon?: string;
  onNavigate?: () => void;
  lg: boolean;
}) {
  return (
    <Link
      href={href}
      scroll={false}
      onClick={onNavigate}
      className={clsx(
        "flex w-full items-center rounded-lg no-underline transition-colors",
        lg ? "min-h-12 gap-3 px-3 text-base" : "min-h-9 gap-2.5 px-2 text-sm",
        isSelected
          ? "bg-(--schemes-blue-50) font-semibold text-(--schemes-blue-600)"
          : "text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50)",
      )}
    >
      {icon && (
        <Image
          src={icon}
          alt=""
          width={lg ? 24 : 20}
          height={lg ? 24 : 20}
          aria-hidden="true"
          className={clsx("shrink-0", lg ? "size-6" : "size-5")}
        />
      )}
      <span className="min-w-0 flex-1 truncate">
        {label}
        {isSelected && (
          <span className="sr-only">
            <Trans comment="Screen-reader suffix on the selected catalogue filter option">
              , selected
            </Trans>
          </span>
        )}
      </span>
      {isSelected && (
        <Check
          size={lg ? 18 : 15}
          strokeWidth={2.5}
          aria-hidden="true"
          className="shrink-0 text-(--schemes-blue-600)"
        />
      )}
    </Link>
  );
}

// Multi-select list of categories or of planning areas. Each row is a Link to
// the catalog with that value toggled: the first category keeps its static
// route, so per-category prerendering and SEO are untouched, and the rest ride
// in the query string.
function FilterList({
  kind,
  selectedCategories,
  selectedAreas,
  onNavigate,
  size,
}: {
  kind: CatalogFilterKind;
  selectedCategories: SchemeCategory[];
  selectedAreas: string[];
  onNavigate: () => void;
  size: "sm" | "lg";
}) {
  const categoryLabel = useCategoryLabel();
  const { t, i18n } = useLingui();
  const lg = size === "lg";
  // Area rows keep the panel open, so a second tap can land before the first
  // navigation commits. Building hrefs from the committed selection would drop
  // the first area; this local copy updates on click. The list remounts each
  // time the panel opens, so it starts from the committed selection.
  const [areas, setAreas] = useState(selectedAreas);
  // "All" leads; the categories follow in alphabetical order of the label shown,
  // using the language's own collation (pinyin order for Chinese).
  const collator = new Intl.Collator(i18n.locale);
  const categories = [
    "All" as const,
    ...CATALOG_CATEGORY_OPTIONS.filter((cat) => cat !== "All").sort((a, b) =>
      collator.compare(categoryLabel(a), categoryLabel(b)),
    ),
  ];

  return (
    <div
      className={clsx(
        "thin-scrollbar min-h-0 flex-1 overflow-y-auto",
        lg ? "p-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))]" : "p-1",
      )}
    >
      {kind === "category" ? (
        categories.map((cat) => (
          <OptionRow
            key={cat}
            lg={lg}
            label={categoryLabel(cat)}
            icon={CATALOG_CATEGORY_ICON_SRC[cat]}
            isSelected={
              cat === "All"
                ? selectedCategories.length === 0
                : selectedCategories.includes(cat)
            }
            href={getCatalogFilterHref(
              cat === "All" ? [] : toggleValue(selectedCategories, cat),
              selectedAreas,
            )}
            // A category change can change the route, which remounts the page.
            onNavigate={onNavigate}
          />
        ))
      ) : (
        <>
          <OptionRow
            lg={lg}
            label={t({
              message: "All areas",
              comment: "Catalogue filter option: no planning area filter",
            })}
            isSelected={areas.length === 0}
            href={getCatalogFilterHref(selectedCategories, [])}
            onNavigate={() => setAreas([])}
          />
          {/* Area rows keep the panel open: the route stays the same, so
              several areas can be picked in one go. */}
          {PLANNING_AREAS.map((area) => (
            <OptionRow
              key={area}
              lg={lg}
              label={planningAreaLabel(i18n, area)}
              isSelected={areas.includes(area)}
              href={getCatalogFilterHref(
                selectedCategories,
                toggleValue(areas, area),
              )}
              onNavigate={() => setAreas(toggleValue(areas, area))}
            />
          ))}
        </>
      )}
    </div>
  );
}

// Category or planning-area picker for the catalog results header. Mirrors
// the schemes-filter affordance: a popover on desktop, a bottom-sheet drawer
// on mobile where popover rows are too small to tap reliably.
function CatalogCategorySelect({
  kind = "category",
  selectedCategories,
  selectedAreas,
  className,
}: CatalogCategorySelectProps) {
  const { t, i18n } = useLingui();
  const categoryLabel = useCategoryLabel();
  const isDesktop = useIsDesktop();
  const drawerState = useOverlayState();
  // Popover is a React Aria DialogTrigger, so it is controlled by isOpen rather
  // than the overlay state object Drawer takes.
  const [popoverOpen, setPopoverOpen] = useState(false);

  const isCategory = kind === "category";
  const primary: CatalogCategory = selectedCategories[0] ?? "All";
  const selected = isCategory ? selectedCategories : selectedAreas;
  const extraCount = Math.max(selected.length - 1, 0);
  const label = isCategory
    ? categoryLabel(primary)
    : selectedAreas[0]
      ? planningAreaLabel(i18n, selectedAreas[0])
      : t({
          message: "All areas",
          comment: "Catalogue filter option: no planning area filter",
        });

  const trigger = (
    <Button
      aria-label={
        isCategory
          ? extraCount
            ? t({
                message: `${label} and ${extraCount} more: browse by category`,
                comment: "Screen-reader label for the catalogue category button; label is the first selected category",
              })
            : t({
                message: `${label}: browse by category`,
                comment: "Screen-reader label for the catalogue category button; label is the selected category",
              })
          : extraCount
            ? t({
                message: `${label} and ${extraCount} more: filter by planning area`,
                comment: "Screen-reader label for the catalogue area button; label is the first selected area",
              })
            : t({
                message: `${label}: filter by planning area`,
                comment: "Screen-reader label for the catalogue area button; label is the selected area",
              })
      }
      className={clsx(
        "inline-flex min-h-11 items-center gap-2 rounded-full border border-(--schemes-border-neutral) bg-white px-4 py-2 text-sm font-semibold text-(--schemes-ink-soft) transition-[background-color,border-color,color] hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
        className,
      )}
    >
      {isCategory ? (
        <Image
          src={CATALOG_CATEGORY_ICON_SRC[primary]}
          alt=""
          width={20}
          height={20}
          aria-hidden="true"
          className="size-5 shrink-0"
        />
      ) : (
        <MapPin
          size={18}
          strokeWidth={2}
          aria-hidden="true"
          className="shrink-0 text-(--schemes-blue-600)"
        />
      )}
      <span className="min-w-0 flex-1 truncate text-left">{label}</span>
      {extraCount > 0 && (
        <span
          aria-hidden="true"
          className="shrink-0 rounded-full bg-(--schemes-blue-50) px-2 text-xs font-semibold text-(--schemes-blue-600)"
        >
          +{extraCount}
        </span>
      )}
      <ChevronDown size={14} strokeWidth={2} className="shrink-0 opacity-70" />
    </Button>
  );

  const list = (size: "sm" | "lg", close: () => void) => (
    <FilterList
      kind={kind}
      selectedCategories={selectedCategories}
      selectedAreas={selectedAreas}
      onNavigate={close}
      size={size}
    />
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
            {list("sm", () => setPopoverOpen(false))}
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
              {isCategory
                ? t({
                    message: "Categories",
                    comment:
                      "Catalogue filter panel heading when choosing categories",
                  })
                : t({
                    message: "Planning area",
                    comment:
                      "Catalogue filter panel heading when choosing a planning area",
                  })}
            </h2>
            {list("lg", () => drawerState.close())}
          </Drawer.Dialog>
        </Drawer.Content>
      </Drawer.Backdrop>
    </Drawer>
  );
}

export default CatalogCategorySelect;
