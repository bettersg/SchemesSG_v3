"use client";
import { useEffect, useRef, useState } from "react";
import { searchSchemes } from "@/lib/schemes";
import { SearchResScheme } from "@/types/types";
import SchemeDrawer from "@/components/schemes/scheme-drawer";
import { Spinner } from "@heroui/react";
import { useInView } from "framer-motion";
import Link from "next/link";
import SchemeCard from "@/components/schemes/scheme-card";

const CATEGORIES = [
  "All", "Financial Assistance", "Mental Health", "Family", "Healthcare",
  "Housing", "Employment", "Food Support", "Education", "Eldercare", "Disability",
];

export default function ExplorePage() {
  const [schemes, setSchemes] = useState<SearchResScheme[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [nextCursor, setNextCursor] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [selectedSchemeId, setSelectedSchemeId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const bottomInView = useInView(bottomRef);

  // Initial load
  useEffect(() => {
    setIsLoading(true);
    searchSchemes(activeCategory === "All" ? "" : activeCategory).then(r => {
      setSchemes(r.schemes);
      setNextCursor(r.nextCursor);
      setTotal(r.total);
      setIsLoading(false);
    });
  }, [activeCategory]);

  // Load more when bottom in view
  useEffect(() => {
    if (bottomInView && nextCursor && !isLoadingMore) {
      setIsLoadingMore(true);
      searchSchemes(activeCategory === "All" ? "" : activeCategory, nextCursor).then(r => {
        setSchemes(prev => [...prev, ...r.schemes]);
        setNextCursor(r.nextCursor);
        setIsLoadingMore(false);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bottomInView]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveCategory("All");
    setIsLoading(true);
    searchSchemes(inputValue).then(r => {
      setSchemes(r.schemes);
      setNextCursor(r.nextCursor);
      setTotal(r.total);
      setSearchQuery(inputValue);
      setIsLoading(false);
    });
  };

  return (
    <div className="bg-[#f4f7fb] relative flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-br from-[#042C53] to-[#185FA5] px-4 sm:px-8 lg:px-16 pt-10 pb-8">
        <div className="max-w-[960px] mx-auto">
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/50 mb-2">Scheme Directory</p>
          <h1 className="font-[var(--font-head)] text-2xl sm:text-3xl font-bold text-white mb-2">Explore all schemes</h1>
          <p className="text-sm text-white/65 mb-5">Browse 500+ social assistance schemes from 200+ agencies across Singapore.</p>
          <form onSubmit={handleSearch} className="flex gap-2 bg-white/12 border border-white/20 rounded-xl px-4 py-2.5 max-w-[520px] backdrop-blur-sm">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="mt-0.5 shrink-0">
              <circle cx="7" cy="7" r="5.5" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5"/>
              <path d="M11 11L14.5 14.5" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <input
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder="Search scheme name or keyword…"
              className="flex-1 bg-transparent text-white placeholder:text-white/50 text-sm outline-none"
            />
            <button type="submit" className="px-3 py-1 rounded-lg bg-[#EF9F27] text-white text-xs font-semibold">Search</button>
          </form>
          <div className="flex gap-5 mt-4 text-xs text-white/60">
            <span><strong className="text-white">{total || "500+"}  </strong>schemes</span>
            <span className="border-l border-white/15 pl-5"><strong className="text-white">200+</strong> agencies</span>
            <span className="border-l border-white/15 pl-5">Updated <strong className="text-white">weekly</strong></span>
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="bg-white border-b border-[#e8eef6] sticky top-[70px] z-10">
        <div className="max-w-[960px] mx-auto px-4 py-2.5 flex gap-2 overflow-x-auto no-scrollbar flex-wrap">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => { setActiveCategory(cat); setInputValue(""); setSearchQuery(""); }}
              className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all border ${
                activeCategory === cat
                  ? "bg-[#185FA5] text-white border-[#185FA5]"
                  : "bg-[#F1EFE8] text-[#5F5E5A] border-[#D3D1C7] hover:bg-[#E6F1FB] hover:text-[#185FA5] hover:border-[#B5D4F4]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      <div className="max-w-[960px] w-full grow mx-auto px-4 sm:px-8 py-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-[#444441]">
            {searchQuery ? `Results for "${searchQuery}"` : activeCategory === "All" ? "All schemes" : activeCategory}
            {!isLoading && <span className="ml-2 text-[#185FA5]">({schemes.length} shown)</span>}
          </p>
          <Link href="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-[#EF9F27] px-3 py-1.5 rounded-lg hover:bg-[#BA7517] transition-colors">
            <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
              <path d="M2 10L12 2M7 2h5v5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Find with AI
          </Link>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-20"><Spinner size="lg" /></div>
        ) : schemes.length === 0 ? (
          <div className="text-center py-20 text-[#B4B2A9]">
            <p className="text-lg mb-2">No schemes found</p>
            <p className="text-sm">Try a different search or category</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {schemes.map(s => (
              <SchemeCard key={s.schemeId} scheme={s} onSelect={() => setSelectedSchemeId(s.schemeId)} />
            ))}
          </div>
        )}

        <div ref={bottomRef} className="flex justify-center py-6">
          {!isLoading && isLoadingMore && <Spinner />}
        </div>

      </div>

		{/* Scheme drawer */}
		<SchemeDrawer schemeId={selectedSchemeId} onClose={() => setSelectedSchemeId(null)} />

    </div>
  );
}
