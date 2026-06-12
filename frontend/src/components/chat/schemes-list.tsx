"use client";
import { useChat } from "@/providers";
import clsx from "clsx";
import SchemeCard from "../schemes/scheme-card";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { ScrollShadow, Spinner } from "@heroui/react";
import { SearchX } from "lucide-react";
import { FilterObjType } from "@/types/types";
import SchemesFilter from "../schemes/schemes-filter";
import { parseArrayString } from "@/lib/utils";
import NewChatButton from "./new-chat-button";
import { StatusTextShimmer } from "./status-text-shimmer";
import { motion, useReducedMotion } from "framer-motion";
import { duration, ease, stagger } from "@/lib/design-system/motion";

// Reveal cards progressively so a large result set (e.g. 193 schemes) doesn't
// mount every card at once. All schemes are already client-side; this is purely
// a rendering window, not a network page.
const PAGE_SIZE = 30;

function EmptySchemesState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-1 items-center justify-center px-4 py-8">
      <div className="w-full max-w-sm rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-5 text-center">
        <div className="mx-auto mb-3 flex size-10 items-center justify-center rounded-full bg-white text-(--schemes-status-info-text)">
          <SearchX size={20} strokeWidth={2} />
        </div>
        <h3 className="text-sm font-semibold text-(--schemes-blue-900)">
          {title}
        </h3>
        <p className="mt-1 text-xs leading-5 text-(--schemes-muted)">
          {description}
        </p>
      </div>
    </div>
  );
}

interface SchemesListProps {
  isGenerating?: boolean;
  handleNewChat?: () => void;
  className?: string;
}

export default function SchemesList({
  isGenerating = false,
  handleNewChat,
  className,
}: SchemesListProps) {
  const { schemes } = useChat();
  const reduceMotion = useReducedMotion();
  const previousSchemeSignatureRef = useRef("");
  const [cardAnimationVersion, setCardAnimationVersion] = useState(0);
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
  const filteredSchemes = useMemo(
    () =>
      schemes.filter((scheme) => {
        if (filterObj.planningArea && filterObj.planningArea.size > 0) {
          if (
            !scheme.planningArea ||
            filterObj.planningArea.intersection(
              new Set(parseArrayString(scheme.planningArea)),
            ).size == 0
          ) {
            return false;
          }
        }
        if (filterObj.agency && filterObj.agency.size > 0) {
          if (!scheme.agency || !filterObj.agency.has(scheme.agency)) {
            return false;
          }
        }
        return true;
      }),
    [schemes, filterObj],
  );
  const schemeSignature = useMemo(
    () => schemes.map((scheme) => scheme.schemeId).join("|"),
    [schemes],
  );
  const hasActiveFilters =
    selectedLocations.size > 0 || selectedAgencies.size > 0;

  // Progressive reveal window over the *filtered* list. Reset to the first page
  // whenever the list identity changes — which happens both on a new agent
  // search (schemes replaced) and on a client filter toggle (filterObj changed),
  // since filteredSchemes is memoized on [schemes, filterObj].
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const lastListRef = useRef(filteredSchemes);
  if (lastListRef.current !== filteredSchemes) {
    // Render-phase reset (React's "adjust state on prop change" pattern): clamps
    // back to the first page before this render commits, so a new large result
    // set never flashes the old, larger visibleCount.
    lastListRef.current = filteredSchemes;
    setVisibleCount(PAGE_SIZE);
  }
  const visibleSchemes = useMemo(
    () => filteredSchemes.slice(0, visibleCount),
    [filteredSchemes, visibleCount],
  );
  const hasMore = visibleCount < filteredSchemes.length;

  const scrollRef = useRef<HTMLDivElement>(null);
  const sentinelRef = useRef<HTMLDivElement>(null);

  // On a new list (new search or filter change), scroll back to the top before
  // paint. Without this, a previously deep-scrolled position would leave the
  // sentinel in view and auto-reveal an extra page, stranding the user mid-list
  // instead of at the top of the fresh results. Layout effect avoids a flash.
  useLayoutEffect(() => {
    scrollRef.current?.scrollTo({ top: 0 });
  }, [filteredSchemes]);

  // Reveal the next page when the sentinel nears the bottom of the scroll area.
  useEffect(() => {
    if (!hasMore) return;
    const root = scrollRef.current;
    const sentinel = sentinelRef.current;
    if (!root || !sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setVisibleCount((count) => count + PAGE_SIZE);
        }
      },
      { root, rootMargin: "0px 0px 200px 0px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, filteredSchemes]);

  useEffect(() => {
    if (
      !schemeSignature ||
      previousSchemeSignatureRef.current === schemeSignature
    ) {
      previousSchemeSignatureRef.current = schemeSignature;
      return;
    }

    previousSchemeSignatureRef.current = schemeSignature;
    setCardAnimationVersion((version) => version + 1);
  }, [schemeSignature]);

  return (
    <div
      className={clsx(
        "h-full w-full max-w-3xl flex-1 border-l border-(--schemes-border) bg-white",
        "flex flex-col overflow-hidden",
        className,
      )}
    >
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between gap-3 border-b border-(--schemes-border) px-4 py-2">
        <div className="min-w-0">
          <div
            role="status"
            aria-live="polite"
            className="mb-0.5 text-sm font-semibold text-(--schemes-blue-600)"
          >
            {isGenerating ? (
              <StatusTextShimmer>Finding the best schemes...</StatusTextShimmer>
            ) : (
              `${filteredSchemes.length} ${filteredSchemes.length === 1 ? "scheme" : "schemes"} found`
            )}
          </div>
          <p className="text-xs text-(--schemes-muted)">
            {isGenerating
              ? ""
              : schemes.length > 0
                ? "Click any scheme to view details"
                : "No matching schemes returned for this chat"}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {!isGenerating && schemes.length > 0 && (
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
          {handleNewChat && (
            <div className="hidden items-center gap-2 md:flex">
              {/* Divider separates the session reset from the filter pills so
                  "New chat" doesn't read as a third filter. */}
              {!isGenerating && schemes.length > 0 && (
                <span
                  aria-hidden="true"
                  className="h-5 w-px bg-(--schemes-border-neutral)"
                />
              )}
              <NewChatButton onPress={handleNewChat} />
            </div>
          )}
        </div>
      </div>

      {/* Scrollable list */}
      {isGenerating ? (
        <div className="flex flex-1 items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : schemes.length === 0 ? (
        <EmptySchemesState
          title="No schemes found"
          description="Try asking with a broader need, fewer conditions, or a different support area."
        />
      ) : filteredSchemes.length === 0 ? (
        <EmptySchemesState
          title="No schemes match the selected filters"
          description={
            hasActiveFilters
              ? "Clear one or more filters to see the schemes from this chat."
              : "Try adjusting the filter options to broaden the list."
          }
        />
      ) : (
        <ScrollShadow
          ref={scrollRef}
          className="thin-scrollbar flex-1 overflow-y-scroll p-3"
        >
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {visibleSchemes.map((scheme, index) => {
              return (
                <motion.div
                  key={`${scheme.schemeId}-${cardAnimationVersion}`}
                  initial={
                    reduceMotion ? false : { opacity: 0, y: 6, scale: 0.985 }
                  }
                  animate={
                    reduceMotion ? undefined : { opacity: 1, y: 0, scale: 1 }
                  }
                  transition={{
                    duration: duration.entrance,
                    ease: ease.outQuart,
                    delay: reduceMotion ? 0 : Math.min(index, 8) * stagger,
                  }}
                  className="col-span-1"
                >
                  <SchemeCard scheme={scheme} />
                </motion.div>
              );
            })}
          </div>
          {hasMore && <div ref={sentinelRef} aria-hidden="true" className="h-px" />}
        </ScrollShadow>
      )}
    </div>
  );
}
