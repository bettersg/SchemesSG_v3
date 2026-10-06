"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { getSchemesCategory } from "@/lib/schemes";
import type { CatalogPageData, Scheme } from "@/types/types";
import { Skeleton, Spinner } from "@heroui/react";
import Link from "next/link";
import SchemeCard from "@/components/schemes/scheme-card";
import { type CatalogCategory } from "@/lib/design-system/categories";
import CatalogCategorySelect from "@/components/catalog/catalog-category-select";
import {
  productCard,
  productPageShell,
} from "@/lib/design-system/product-styles";
import EmptyState from "@/components/feedback/empty-state";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import { Search } from "lucide-react";

type CatalogLoadState =
  | "loadingInitial"
  | "ready"
  | "loadingMore"
  | "exhausted";

type CatalogPageClientProps = {
  initialCategory: CatalogCategory;
  initialData?: CatalogPageData;
};

function CatalogGridSkeleton() {
  return (
    <div
      aria-label="Loading schemes"
      className="mx-auto grid grid-cols-1 gap-4 sm:grid-cols-2 lg:max-w-[68rem] lg:grid-cols-3 2xl:max-w-none 2xl:grid-cols-4"
    >
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className={`${productCard} flex min-h-[172px] flex-col gap-3 p-4`}
        >
          {/* Mirrors SchemeCard: 64px logo against three rows (name, agency,
              one chip), then the summary. */}
          <div className="flex items-start gap-3">
            <Skeleton className="h-16 w-16 shrink-0 rounded-lg" />
            <div className="flex min-w-0 flex-1 flex-col gap-1.5">
              <Skeleton className="h-3.5 w-4/5 rounded-full" />
              <Skeleton className="h-3 w-1/2 rounded-full" />
              <Skeleton className="h-5 w-24 rounded-full" />
            </div>
          </div>
          <div className="flex flex-col gap-2">
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
  initialData,
}: CatalogPageClientProps) {
  const activeCategory = initialCategory;
  // The route hands over its server read, so hydration can render the first
  // page without fetching it again.
  const hasInitialData = initialData !== undefined;
  const initialLoadState: CatalogLoadState = !hasInitialData
    ? "loadingInitial"
    : initialData?.nextCursor
      ? "ready"
      : "exhausted";
  const [schemes, setSchemes] = useState<Scheme[]>(
    hasInitialData ? (initialData?.schemes ?? []) : [],
  );
  const [totalCount, setTotalCount] = useState<number | null>(
    hasInitialData ? (initialData?.total ?? null) : null,
  );
  const [loadState, setLoadState] =
    useState<CatalogLoadState>(initialLoadState);

  // states for search feature (tbc)
  // const [searchQuery, setSearchQuery] = useState("");
  // const [inputValue, setInputValue] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef(
    hasInitialData ? (initialData?.nextCursor ?? "") : "",
  );
  const requestIdRef = useRef(0);
  const hasUserScrolledRef = useRef(false);
  const isLoadingInitial = loadState === "loadingInitial";
  const isLoadingMore = loadState === "loadingMore";

  const loadMoreSchemes = useCallback(() => {
    const cursor = cursorRef.current;
    if (loadState !== "ready" || !cursor || !hasUserScrolledRef.current) {
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    hasUserScrolledRef.current = false;
    setLoadState("loadingMore");

    const category =
      activeCategory === "All" ? "" : activeCategory.toLowerCase();
    getSchemesCategory(category, cursor)
      .then((r) => {
        if (requestIdRef.current !== requestId) return;
        setSchemes((prev) => [...prev, ...r.schemes]);
        cursorRef.current = r.nextCursor;
        setLoadState(r.nextCursor ? "ready" : "exhausted");
      })
      .catch(() => {
        if (requestIdRef.current === requestId) {
          setLoadState(cursorRef.current ? "ready" : "exhausted");
        }
      });
  }, [
    activeCategory,
    loadState,
    // searchQuery
  ]);

  useEffect(() => {
    const root = scrollRef.current;
    const target = bottomRef.current;
    if (!root || !target) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasUserScrolledRef.current) {
          loadMoreSchemes();
        }
      },
      {
        root,
        rootMargin: "0px 0px 240px 0px",
      },
    );

    observer.observe(target);

    return () => {
      observer.disconnect();
    };
  }, [loadMoreSchemes]);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root) return;

    const handleScroll = () => {
      if (root.scrollTop > 0) {
        hasUserScrolledRef.current = true;
      }
      if (root.scrollHeight - root.scrollTop - root.clientHeight < 320) {
        loadMoreSchemes();
      }
    };

    root.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      root.removeEventListener("scroll", handleScroll);
    };
  }, [loadMoreSchemes]);

  useEffect(() => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    hasUserScrolledRef.current = false;
    scrollRef.current?.scrollTo({ top: 0 });

    if (hasInitialData && initialData) {
      setSchemes(initialData.schemes);
      setTotalCount(initialData.total);
      cursorRef.current = initialData.nextCursor;
      setLoadState(initialData.nextCursor ? "ready" : "exhausted");
      return;
    }

    cursorRef.current = "";
    setLoadState("loadingInitial");
    setTotalCount(null);
    getSchemesCategory(
      activeCategory === "All" ? "" : activeCategory.toLowerCase(),
    ).then((r) => {
      if (requestIdRef.current !== requestId) return;
      setSchemes(r.schemes);
      setTotalCount(r.total);
      cursorRef.current = r.nextCursor;
      setLoadState(r.nextCursor ? "ready" : "exhausted");
    });
  }, [activeCategory, hasInitialData, initialData]);

  // search feature (tbc)
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

      <div className="flex">
        {/* max-w-7xl with the navbar's px-6, so the grid's outer edge lines up
            with the nav and footer on wide screens. Wider than the shared
            productPageContent (max-w-5xl) on purpose: that cap protects the
            65-75ch reading measure on prose pages, and a card grid has no prose
            to protect. Prose routes stay at 5xl. */}
        <div className="mx-auto max-w-7xl flex-1 px-4 sm:px-6">
          <div className="sticky top-0 z-20 bg-(--schemes-bg) pb-4 pt-2 sm:pb-3">
            {/* The count reads first on desktop and the controls sit opposite
                it; on mobile the controls come first, so the count stays
                directly above the grid it describes. */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
              <h1 className="order-2 font-(--font-head) text-xl font-semibold text-(--schemes-blue-900) sm:order-none sm:text-2xl">
                {isLoadingInitial ? (
                  <StatusTextShimmer>
                    {activeCategory === "All"
                      ? "Finding schemes across all categories..."
                      : `Finding ${activeCategory} schemes...`}
                  </StatusTextShimmer>
                ) : (
                  <>
                    {activeCategory === "All" ? "All schemes" : activeCategory}
                    <span className="ml-2 align-middle text-sm font-semibold text-(--schemes-blue-600)">
                      {totalCount !== null && schemes.length < totalCount
                        ? `(${schemes.length} of ${totalCount})`
                        : `(${totalCount ?? schemes.length})`}
                    </span>
                  </>
                )}
              </h1>
              <div className="order-1 flex shrink-0 items-center gap-2 sm:order-none">
                {/* Names the dimension: the h1 already states the active
                    category, so an unlabelled trigger reads as a badge. */}
                <span className="shrink-0 text-xs font-semibold uppercase tracking-wide text-(--schemes-muted)">
                  Category
                </span>
                {/* Fills the row on mobile, content-width from sm up. Width
                    rather than flex-basis: HeroUI's button base is w-fit, and a
                    flex-1 basis of 0 fights it. */}
                <CatalogCategorySelect
                  activeCategory={activeCategory}
                  className="w-full sm:w-auto"
                />
                <Link
                  href="/"
                  aria-label="Search schemes"
                  className="inline-flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border border-(--schemes-blue-100) bg-(--schemes-blue-50) px-4 py-2 text-sm font-semibold text-(--schemes-blue-600) transition-[background-color,border-color,color] hover:border-(--schemes-blue-600) hover:bg-(--schemes-blue-600) hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)"
                >
                  <Search size={18} strokeWidth={2} />
                  Search
                </Link>
              </div>
            </div>
          </div>
          {isLoadingInitial ? (
            <CatalogGridSkeleton />
          ) : schemes.length === 0 ? (
            <EmptyState
              title="No schemes found"
              description="Try a different search or category"
            />
          ) : (
            <div className="mx-auto grid grid-cols-1 gap-4 sm:grid-cols-2 lg:max-w-[68rem] lg:grid-cols-3 2xl:max-w-none 2xl:grid-cols-4">
              {schemes.map((s, index) => (
                <SchemeCard
                  key={s.schemeId}
                  scheme={s}
                  headingLevel={2}
                  list={{ id: "catalog", index }}
                />
              ))}
            </div>
          )}
          <div ref={bottomRef} className="flex justify-center py-6">
            {isLoadingMore && <Spinner />}
          </div>
        </div>
      </div>
    </div>
  );
}
