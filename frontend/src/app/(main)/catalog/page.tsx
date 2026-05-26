"use client";
import { useEffect, useRef, useState } from "react";
import { searchSchemes } from "@/lib/schemes";
import { Scheme } from "@/types/types";
import { Spinner } from "@heroui/react";
import { motion, useInView } from "framer-motion";
import Link from "next/link";
import SchemeCard from "@/components/schemes/scheme-card";
import { SCHEME_CATEGORIES } from "@/lib/design-system/categories";
import {
  productButtonPrimary,
  productButtonSm,
  productCard,
  productHeading,
  productPageContent,
  productPageShell,
  productSubheading,
} from "@/lib/design-system/product-styles";
import { ArrowUpRight } from "lucide-react";

const CATEGORIES = ["All", ...SCHEME_CATEGORIES] as const;

export default function ExplorePage() {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [nextCursor, setNextCursor] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [hasSelectedCategory, setHasSelectedCategory] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [inputValue, setInputValue] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const bottomInView = useInView(bottomRef);

  // Initial load
  useEffect(() => {
    if (!hasSelectedCategory) return;
    setIsLoading(true);
    searchSchemes(activeCategory === "All" ? "" : activeCategory).then((r) => {
      setSchemes(r.schemes);
      setNextCursor(r.nextCursor);
      setTotal(r.total);
      setIsLoading(false);
    });
  }, [activeCategory, hasSelectedCategory]);

  // Load more when bottom in view
  useEffect(() => {
    if (bottomInView && nextCursor && !isLoadingMore) {
      setIsLoadingMore(true);
      searchSchemes(
        activeCategory === "All" ? "" : activeCategory,
        nextCursor,
      ).then((r) => {
        setSchemes((prev) => [...prev, ...r.schemes]);
        setNextCursor(r.nextCursor);
        setIsLoadingMore(false);
      });
    }
  }, [bottomInView]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveCategory("All");
    setHasSelectedCategory(true);
    setIsLoading(true);
    searchSchemes(inputValue).then((r) => {
      setSchemes(r.schemes);
      setNextCursor(r.nextCursor);
      setTotal(r.total);
      setSearchQuery(inputValue);
      setIsLoading(false);
    });
  };

  const handleSelectCategory = (label: string) => {
    setActiveCategory(label);
    setHasSelectedCategory(true);
    setInputValue("");
    setSearchQuery("");
  };

  if (!hasSelectedCategory) {
    return (
      <div className={productPageShell}>
        <div className={productPageContent}>
          <p className="mb-2 text-[10px] font-semibold tracking-widest text-(--schemes-muted) uppercase">
            Scheme Directory
          </p>
          <h1 className={`${productHeading} mb-2`}>Explore all schemes</h1>
          <p className={`${productSubheading} mb-8`}>
            Pick a category to browse social assistance schemes available in
            Singapore.
          </p>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => handleSelectCategory(cat)}
                className={`${productCard} group flex flex-col items-start gap-3 p-5 text-left transition-[border-color,box-shadow,transform,color,background-color] hover:-translate-y-0.5 hover:border-(--schemes-blue-100) hover:shadow-[0_4px_20px_rgba(24,95,165,0.08)]`}
              >
                <span className="text-sm font-semibold text-(--schemes-blue-900) group-hover:text-(--schemes-blue-600)">
                  {cat === "All" ? "All Schemes" : cat}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${productPageShell} relative flex flex-col`}>
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
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => handleSelectCategory(cat)}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-[background-color,border-color,color] ${
                activeCategory === cat
                  ? "border-(--schemes-blue-600) bg-(--schemes-blue-600) text-white"
                  : "border-(--schemes-border-neutral) bg-white text-(--schemes-muted) hover:border-(--schemes-blue-100) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <motion.div className="flex">
        {/* Results */}
        <div className="mx-auto max-w-5xl flex-1 px-4 py-6 sm:px-8">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm font-semibold text-(--schemes-ink-soft)">
              {searchQuery
                ? `Results for "${searchQuery}"`
                : activeCategory === "All"
                  ? "All schemes"
                  : activeCategory}
              {!isLoading && (
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
          {isLoading ? (
            <div className="flex justify-center py-20">
              <Spinner size="lg" />
            </div>
          ) : schemes.length === 0 ? (
            <div className="py-20 text-center text-(--schemes-muted)">
              <p className="mb-2 text-lg">No schemes found</p>
              <p className="text-sm">Try a different search or category</p>
            </div>
          ) : (
            <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
              {schemes.map((s) => (
                <SchemeCard key={s.schemeId} scheme={s} />
              ))}
            </div>
          )}
          <div ref={bottomRef} className="flex justify-center py-6">
            {!isLoading && isLoadingMore && <Spinner />}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
