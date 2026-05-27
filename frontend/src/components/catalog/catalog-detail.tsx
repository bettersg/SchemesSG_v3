"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { getSchemesCategory, searchSchemes } from "@/lib/schemes";
import { Scheme } from "@/types/types";
import { Spinner } from "@heroui/react";
import Link from "next/link";
import Image from "next/image";
import SchemeCard from "@/components/schemes/scheme-card";
import {
  CATALOG_CATEGORY_OPTIONS,
  CATALOG_CATEGORY_SLUGS,
  type CatalogCategory,
} from "@/lib/design-system/categories";
import {
  productButtonPrimary,
  productButtonSm,
  productCard,
  productHeading,
  productPageShell,
  productSubheading,
} from "@/lib/design-system/product-styles";
import PageShell from "@/components/layout/page-shell";
import EmptyState from "@/components/feedback/empty-state";
import { ArrowUpRight } from "lucide-react";

type CatalogPageClientProps = {
  initialCategory?: CatalogCategory;
};

type CatalogLoadState =
  | "idle"
  | "loadingInitial"
  | "ready"
  | "loadingMore"
  | "exhausted";

const CATALOG_CATEGORY_ICON_SRC: Record<CatalogCategory, string> = {
  All: "/catalog/Schemes_Icons_All.svg",
  Disability: "/catalog/Schemes_Icons_Disability.svg",
  Education: "/catalog/Schemes_Icons_Education.svg",
  Eldercare: "/catalog/Schemes_Icons_Eldercare.svg",
  Employment: "/catalog/Schemes_Icons_Employment.svg",
  Family: "/catalog/Schemes_Icons_Family.svg",
  "Financial Assistance": "/catalog/Schemes_Icons_Financial Assistance.svg",
  "Food Support": "/catalog/Schemes_Icons_Food Support.svg",
  Healthcare: "/catalog/Schemes_Icons_Healthcare.svg",
  Housing: "/catalog/Schemes_Icons_Housing.svg",
  "Mental Health": "/catalog/Schemes_Icons_Mental Health.svg",
};

function CatalogGridSkeleton() {
  return (
    <div
      aria-label="Loading schemes"
      className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4"
    >
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className={`${productCard} flex min-h-[172px] animate-pulse flex-col gap-3 p-4`}
        >
          <div className="flex items-start gap-2.5">
            <div className="h-10 w-10 shrink-0 rounded-lg " />
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <div className="h-3.5 w-4/5 rounded-full " />
              <div className="h-3 w-1/2 rounded-full " />
            </div>
          </div>
          <div className="flex gap-1.5">
            <div className="h-5 w-20 rounded-full " />
            <div className="h-5 w-24 rounded-full " />
          </div>
          <div className="mt-auto flex flex-col gap-2">
            <div className="h-3 w-full rounded-full " />
            <div className="h-3 w-5/6 rounded-full " />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function CatalogPageClient({
  initialCategory,
}: CatalogPageClientProps) {
  const [activeCategory, setActiveCategory] = useState(
    initialCategory ?? "All",
  );
  const [hasSelectedCategory, setHasSelectedCategory] = useState(
    Boolean(initialCategory),
  );
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [loadState, setLoadState] = useState<CatalogLoadState>(
    initialCategory ? "loadingInitial" : "idle",
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [inputValue, setInputValue] = useState("");

  // load more schemes when user scrolls to bottom
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef("");
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

    const request = searchQuery
      ? searchSchemes(searchQuery, cursor)
      : getSchemesCategory(
          activeCategory === "All" ? "" : activeCategory,
          cursor,
        );

    request
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
  }, [activeCategory, loadState, searchQuery]);

  useEffect(() => {
    const root = scrollRef.current;
    const target = bottomRef.current;
    if (!hasSelectedCategory || !root || !target) return;

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
  }, [hasSelectedCategory, loadMoreSchemes]);

  useEffect(() => {
    const root = scrollRef.current;
    if (!hasSelectedCategory || !root) return;

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
  }, [hasSelectedCategory, loadMoreSchemes]);

  // Initial load
  useEffect(() => {
    if (!hasSelectedCategory) return;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    hasUserScrolledRef.current = false;
    cursorRef.current = "";
    scrollRef.current?.scrollTo({ top: 0 });
    setLoadState("loadingInitial");
    getSchemesCategory(activeCategory === "All" ? "" : activeCategory).then(
      (r) => {
        if (requestIdRef.current !== requestId) return;
        setSchemes(r.schemes);
        cursorRef.current = r.nextCursor;
        setLoadState(r.nextCursor ? "ready" : "exhausted");
      },
    );
  }, [activeCategory, hasSelectedCategory]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    hasUserScrolledRef.current = false;
    cursorRef.current = "";
    scrollRef.current?.scrollTo({ top: 0 });
    setActiveCategory("All");
    setHasSelectedCategory(true);
    setLoadState("loadingInitial");
    searchSchemes(inputValue).then((r) => {
      if (requestIdRef.current !== requestId) return;
      setSchemes(r.schemes);
      cursorRef.current = r.nextCursor;
      setSearchQuery(inputValue);
      setLoadState(r.nextCursor ? "ready" : "exhausted");
    });
  };

  if (!hasSelectedCategory) {
    return (
      <PageShell>
        <p className="mb-2 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase">
          Scheme Directory
        </p>
        <h1 className={`${productHeading} mb-2`}>Explore all schemes</h1>
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
      {/* Header */}
      {/* <div className="bg-gradient-to-br from-[#042C53] to-[#185FA5] px-4 sm:px-8 lg:px-16 pt-10 pb-8">
        <div className="max-w-[960px] mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/50 mb-2">
            Scheme Directory
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
        <div className="no-scrollbar mx-auto flex max-w-5xl flex-wrap gap-2 overflow-x-auto px-4 py-2.5 sm:px-8">
          {CATALOG_CATEGORY_OPTIONS.map((cat) => (
            <Link
              key={cat}
              href={`/catalog/${CATALOG_CATEGORY_SLUGS[cat]}`}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-[background-color,border-color,color] ${
                activeCategory === cat
                  ? "border-(--schemes-blue-600) bg-(--schemes-blue-600) text-white"
                  : "border-(--schemes-border-neutral) bg-white text-(--schemes-muted) hover:border-(--schemes-blue-100) hover: hover:text-(--schemes-blue-600)"
              }`}
            >
              {cat}
            </Link>
          ))}
        </div>
      </div>

      <div className="flex">
        {/* Results */}
        <div className="mx-auto max-w-5xl flex-1 px-4 sm:px-8">
          <div className="bg-(--schemes-bg) py-4 flex items-center justify-between sticky top-0 z-20">
            <p className="text-sm font-semibold text-(--schemes-ink-soft)">
              {searchQuery
                ? `Results for "${searchQuery}"`
                : activeCategory === "All"
                  ? "All schemes"
                  : activeCategory}
              {!isLoadingInitial && (
                <span className="ml-2 text-(--schemes-blue-600)">
                  ({schemes.length} shown)
                </span>
              )}
            </p>
            <Link
              href="/"
              className={`${productButtonPrimary} ${productButtonSm}`}
            >
              <ArrowUpRight size={14} strokeWidth={2} />
              Find with AI
            </Link>
          </div>
          {isLoadingInitial ? (
            <CatalogGridSkeleton />
          ) : schemes.length === 0 ? (
            <EmptyState
              title="No schemes found"
              description="Try a different search or category"
            />
          ) : (
            <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
              {schemes.map((s) => (
                <SchemeCard key={s.schemeId} scheme={s} />
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
