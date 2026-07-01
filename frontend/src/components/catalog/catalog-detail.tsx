"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { getSchemesCategory } from "@/lib/schemes";
import { FilterObjType, Scheme } from "@/types/types";
import { ScrollShadow, Skeleton } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import SchemeCard from "@/components/schemes/scheme-card";
import SchemesFilter from "@/components/schemes/schemes-filter";
import { matchesSchemeFilters } from "@/lib/matches-scheme-filters";
import {
  CATALOG_CATEGORY_ICON_SRC,
  CATALOG_CATEGORY_OPTIONS,
  CATALOG_CATEGORY_SLUGS,
  type CatalogCategory,
} from "@/lib/design-system/categories";
import CatalogCategoryDrawer from "@/components/catalog/catalog-category-drawer";
import {
  productCard,
  productHeading,
  productPageShell,
  productSubheading,
} from "@/lib/design-system/product-styles";
import PageShell from "@/components/layout/page-shell";
import EmptyState from "@/components/feedback/empty-state";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import { Search } from "lucide-react";

// Upper bound on schemes fetched per catalog view. The full catalog is ~495
// and the largest category ~300, so one request returns everything and the
// Location/Agency filters run client-side over the whole set.
const CATALOG_FETCH_LIMIT = 600;

type CatalogPageClientProps = {
  initialCategory?: CatalogCategory;
};

type CatalogLoadState =
  | "idle"
  | "loadingInitial"
  | "ready"
  | "loadingMore"
  | "exhausted";

function CatalogGridSkeleton() {
  return (
    <div
      aria-label="Loading schemes"
      className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4"
    >
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className={`${productCard} flex min-h-[172px] flex-col gap-3 p-4`}
        >
          <div className="flex items-start gap-2.5">
            <Skeleton className="h-10 w-10 shrink-0 rounded-lg" />
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <Skeleton className="h-3.5 w-4/5 rounded-full" />
              <Skeleton className="h-3 w-1/2 rounded-full" />
            </div>
          </div>
          <div className="flex gap-1.5">
            <Skeleton className="h-5 w-20 rounded-full" />
            <Skeleton className="h-5 w-24 rounded-full" />
          </div>
          <div className="mt-auto flex flex-col gap-2">
            <Skeleton className="h-3 w-full rounded-full" />
            <Skeleton className="h-3 w-5/6 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function CatalogPageClient({
  initialCategory,
}: CatalogPageClientProps) {
  const [activeCategory] = useState(initialCategory ?? "All");
  const hasSelectedCategory = Boolean(initialCategory);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [loadState, setLoadState] = useState<CatalogLoadState>(
    initialCategory ? "loadingInitial" : "idle",
  );

  // Location/Agency filters, applied client-side over the fully-loaded set —
  // the same model as the chat results view. The catalog is small enough
  // (≤~300 per category, 495 total) to load whole and filter in memory, which
  // sidesteps Firestore's one-array-clause-per-query limit on combining
  // category + planning_area.
  const [filterObj, setFilterObj] = useState<FilterObjType>({});
  const [selectedLocations, setSelectedLocations] = useState<Set<string>>(
    new Set(),
  );
  const [selectedAgencies, setSelectedAgencies] = useState<Set<string>>(
    new Set(),
  );
  const resetFilters = () => {
    setSelectedLocations(new Set());
    setSelectedAgencies(new Set());
    setFilterObj({});
  };

  const scrollRef = useRef<HTMLDivElement>(null);
  const requestIdRef = useRef(0);
  const isLoadingInitial = loadState === "loadingInitial";

  const filteredSchemes = useMemo(
    () => schemes.filter((scheme) => matchesSchemeFilters(scheme, filterObj)),
    [schemes, filterObj],
  );
  const hasActiveFilters =
    selectedLocations.size > 0 || selectedAgencies.size > 0;
  // Client-side filtering only covers the schemes we loaded. Today the whole
  // catalog fits under CATALOG_FETCH_LIMIT, but if the collection grows past it
  // a category could be truncated — surface that rather than filter silently
  // over a partial set. (Signal to migrate to server-side filtering.)
  const isCapped = totalCount !== null && schemes.length < totalCount;

  // Load the whole category (or all schemes) in one request, then filter
  // client-side. CATALOG_FETCH_LIMIT comfortably exceeds the largest category.
  useEffect(() => {
    if (!hasSelectedCategory) return;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    scrollRef.current?.scrollTo({ top: 0 });
    setLoadState("loadingInitial");
    setTotalCount(null);
    getSchemesCategory(
      activeCategory === "All" ? "" : activeCategory.toLowerCase(),
      "",
      CATALOG_FETCH_LIMIT,
    ).then((r) => {
      if (requestIdRef.current !== requestId) return;
      setSchemes(r.schemes);
      setTotalCount(r.total);
      setLoadState("exhausted");
    });
  }, [activeCategory, hasSelectedCategory]);

  if (!hasSelectedCategory) {
    return (
      <PageShell>
        <h1 className={`${productHeading} mb-2`}>
          Explore our schemes collection
        </h1>
        <p className={`${productSubheading} mb-8`}>
          Pick a category to browse social assistance schemes available in
          Singapore.
        </p>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
          {CATALOG_CATEGORY_OPTIONS.map((cat) => (
            <Link
              key={cat}
              href={`/catalog/${CATALOG_CATEGORY_SLUGS[cat]}`}
              className={`${productCard} group flex items-center gap-3 p-4 text-left transition-[border-color,box-shadow,transform,color,background-color] hover:-translate-y-0.5 hover:border-(--schemes-blue-100) hover:shadow-[0_4px_20px_rgba(24,95,165,0.08)] sm:p-5`}
            >
              <Image
                src={CATALOG_CATEGORY_ICON_SRC[cat]}
                alt=""
                width={40}
                height={40}
                aria-hidden="true"
                className="h-10 w-10 shrink-0"
              />
              <span className="text-sm font-semibold text-(--schemes-blue-900) group-hover:text-(--schemes-blue-600)">
                {cat === "All" ? "All Schemes" : cat}
              </span>
            </Link>
          ))}
        </div>
      </PageShell>
    );
  }

  return (
    <div
      ref={scrollRef}
      className={`${productPageShell} relative flex flex-col`}
    >
      {/* Header with Search Bar */}
      {/* <div className="bg-gradient-to-br from-[#042C53] to-[#185FA5] px-4 sm:px-8 lg:px-16 pt-10 pb-8">
        <div className="max-w-[960px] mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/50 mb-2">
            Scheme Catalog
          </p>
          <h1 className="mb-2 font-(--font-head) text-2xl font-bold text-white sm:text-3xl">
            Explore all schemes
          </h1>
          <p className="text-sm text-white/65 mb-5">
            Browse 500+ social assistance schemes from 200+ agencies across
            Singapore.
          </p>
          <form
            onSubmit={handleSearch}
            className="flex gap-2 bg-white/12 border border-white/20 rounded-xl px-4 py-2.5 max-w-[520px] backdrop-blur-sm"
          >
            <Search
              size={16}
              strokeWidth={1.5}
              className="mt-0.5 shrink-0 text-white/60"
            />
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Search scheme name or keyword…"
              className="flex-1 bg-transparent text-white placeholder:text-white/50 text-sm outline-none"
            />
            <button
              type="submit"
              className="px-3 py-1 rounded-lg bg-[#EF9F27] text-white text-xs font-semibold"
            >
              Search
            </button>
          </form>
          <div className="flex gap-5 mt-4 text-xs text-white/60">
            <span>
              <strong className="text-white">{total || "500+"} </strong>schemes
            </span>
            <span className="border-l border-white/15 pl-5">
              <strong className="text-white">200+</strong> agencies
            </span>
            <span className="border-l border-white/15 pl-5">
              Updated <strong className="text-white">weekly</strong>
            </span>
          </div>
        </div>
      </div> */}

      {/* Filter bar */}
      <div className="z-10">
        {/* Mobile (<md): collapse the chip row into a single-select category
            drawer trigger, with the Search mode-switch beside it. */}
        <div className="mx-auto flex max-w-5xl items-center gap-2 px-4 py-2.5 md:hidden">
          <CatalogCategoryDrawer activeCategory={activeCategory} />
          <Link
            href="/"
            aria-label="Search schemes"
            className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border border-(--schemes-blue-100) bg-(--schemes-blue-50) px-4 py-2 text-sm font-semibold text-(--schemes-blue-600) transition-[background-color,border-color,color] hover:border-(--schemes-blue-600) hover:bg-(--schemes-blue-600) hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)"
          >
            <Search size={18} strokeWidth={2} />
            Search
          </Link>
        </div>
        {/* Desktop (md+): the original horizontal category chip row. */}
        <ScrollShadow
          orientation="horizontal"
          className="no-scrollbar mx-auto hidden max-w-5xl flex-wrap gap-2 overflow-x-auto px-4 py-2.5 sm:px-8 md:flex"
        >
          {CATALOG_CATEGORY_OPTIONS.map((cat) => (
            <Link
              key={cat}
              href={`/catalog/${CATALOG_CATEGORY_SLUGS[cat]}`}
              className={`inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-xs font-semibold transition-[background-color,border-color,color] ${
                activeCategory === cat
                  ? "border-(--schemes-blue-600) bg-(--schemes-blue-600) text-white"
                  : "border-(--schemes-border-neutral) bg-white text-(--schemes-muted) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600)"
              }`}
            >
              {cat}
            </Link>
          ))}
          {/* Mode switch: browse categories here, or search conversationally.
              Same chip shape as the categories so it flows in the row; tinted
              blue with a search icon so it reads as a control, not a category. */}
          <Link
            href="/"
            aria-label="Search schemes"
            className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border border-(--schemes-blue-100) bg-(--schemes-blue-50) px-3.5 py-2 text-xs font-semibold text-(--schemes-blue-600) transition-[background-color,border-color,color] hover:border-(--schemes-blue-600) hover:bg-(--schemes-blue-600) hover:text-white"
          >
            <Search size={15} strokeWidth={2} />
            Search
          </Link>
        </ScrollShadow>
      </div>

      <div className="flex">
        {/* Results */}
        <div className="mx-auto max-w-5xl flex-1 px-4 sm:px-8">
          <div className="sticky top-0 z-20 flex items-center justify-between gap-3 bg-(--schemes-bg) pb-3 pt-2">
            <p className="text-sm font-semibold text-(--schemes-ink-soft)">
              {isLoadingInitial ? (
                <StatusTextShimmer>
                  {activeCategory === "All"
                    ? "Finding schemes across all categories..."
                    : `Finding ${activeCategory} schemes...`}
                </StatusTextShimmer>
              ) : (
                <>
                  {activeCategory === "All" ? "All schemes" : activeCategory}
                  <span className="ml-2 text-(--schemes-blue-600)">
                    {hasActiveFilters
                      ? `(${filteredSchemes.length} of ${totalCount ?? schemes.length})`
                      : `(${totalCount ?? schemes.length})`}
                  </span>
                </>
              )}
            </p>
            {!isLoadingInitial && schemes.length > 0 && (
              <SchemesFilter
                schemes={schemes}
                setFilterObj={setFilterObj}
                selectedLocations={selectedLocations}
                setSelectedLocations={setSelectedLocations}
                selectedAgencies={selectedAgencies}
                setSelectedAgencies={setSelectedAgencies}
                resetFilters={resetFilters}
              />
            )}
          </div>
          {!isLoadingInitial && isCapped && (
            <p className="mb-3 rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) px-3 py-2 text-xs text-(--schemes-status-info-text)">
              Showing the first {schemes.length} of {totalCount}. Filters apply
              to these for now.
            </p>
          )}
          {isLoadingInitial ? (
            <CatalogGridSkeleton />
          ) : filteredSchemes.length === 0 ? (
            <EmptyState
              title="No schemes found"
              description={
                hasActiveFilters
                  ? "Try clearing a filter or choosing a different area or agency."
                  : "Try a different category."
              }
            />
          ) : (
            <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4 pb-6">
              {filteredSchemes.map((s) => (
                <SchemeCard key={s.schemeId} scheme={s} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
