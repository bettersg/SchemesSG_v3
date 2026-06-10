"use client";
import { useChat } from "@/providers";
import clsx from "clsx";
import SchemeCard from "../schemes/scheme-card";
import { useEffect, useMemo, useRef, useState } from "react";
import { ScrollShadow, Spinner } from "@heroui/react";
import { SearchX } from "lucide-react";
import { FilterObjType } from "@/types/types";
import SchemesFilter from "../schemes/schemes-filter";
import { parseArrayString } from "@/lib/utils";
import NewChatButton from "./new-chat-button";
import { StatusTextShimmer } from "./status-text-shimmer";
import { motion, useReducedMotion } from "framer-motion";
import { duration, ease, stagger } from "@/lib/design-system/motion";

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
  selectedSchemeId?: string | null;
  onSelectScheme?: (schemeId: string) => void;
}

export default function SchemesList({
  isGenerating = false,
  handleNewChat,
  className,
  selectedSchemeId,
  onSelectScheme,
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
      <div className="flex shrink-0 items-center justify-between border-b border-(--schemes-border) px-4 py-2">
        <div className="min-w-0">
          <div
            role="status"
            aria-live="polite"
            className="mb-0.5 text-sm font-semibold text-(--schemes-blue-600)"
          >
            {isGenerating ? (
              <StatusTextShimmer>Finding the best schemes...</StatusTextShimmer>
            ) : (
              `${schemes.length} ${schemes.length === 1 ? "scheme" : "schemes"} found`
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
              mode="compact"
              className="lg:hidden"
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
            <div className="hidden md:block">
              <NewChatButton onPress={handleNewChat} />
            </div>
          )}
        </div>
      </div>

      {/* Filter */}
      {schemes.length > 0 && (
        <SchemesFilter
          mode="toolbar"
          className="hidden lg:flex"
          schemes={schemes}
          setFilterObj={setFilterObj}
          selectedLocations={selectedLocations}
          setSelectedLocations={setSelectedLocations}
          selectedAgencies={selectedAgencies}
          setSelectedAgencies={setSelectedAgencies}
          resetFilters={resetFilters}
        />
      )}

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
        <ScrollShadow className="thin-scrollbar flex-1 overflow-y-scroll p-2">
          <div className="grid grid-cols-1 gap-1 lg:grid-cols-2">
            {filteredSchemes.map((scheme, index) => {
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
                // <button
                //   key={scheme.schemeId}
                //   onClick={() => onSelectScheme(scheme.schemeId)}
                //   className={`w-full text-left rounded-lg border-[1.5px] px-3 py-2.5 mb-1.5 transition-all relative ${
                //     isActive
                //       ? "border-[#378ADD] bg-[#E6F1FB]"
                //       : "border-[#e0eaf5] bg-white hover:border-[#B5D4F4] hover:bg-[#f0f6ff]"
                //   }`}
                // >
                //   {isActive && (
                //     <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#378ADD] rounded-l-lg" />
                //   )}
                //   <div className="text-[9.5px] text-[#B4B2A9] mb-0.5 truncate">{scheme.agency}</div>
                //   <div className="text-[11.5px] font-semibold text-[#042C53] leading-snug mb-1.5 line-clamp-2">
                //     {scheme.schemeName}
                //   </div>
                //   <div className="flex gap-1 flex-wrap">
                //     {types.map((t) => <CategoryTag key={t} label={t} />)}
                //   </div>
                // </button>
              );
            })}
          </div>
        </ScrollShadow>
      )}

      {/* Footer */}
      {/* <Link
        href="/explore"
        className="block text-center py-2.5 text-[11px] text-[#378ADD] font-medium border-t border-[#eef2f7] hover:bg-[#f7f9fc] transition-colors shrink-0"
      >
        Browse all {totalCount} schemes →
      </Link> */}
    </div>
  );
}
