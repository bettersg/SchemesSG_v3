"use client";

import { Spacer, Spinner } from "@heroui/react";
import SchemeCard from "./scheme-card";
import SchemesFilter from "./schemes-filter";
import {
  Dispatch,
  SetStateAction,
  useEffect,
  useRef,
  useState,
  useMemo,
} from "react";
import { useInView } from "framer-motion";
import { useChat } from "@/app/providers";
import { FilterObjType } from "@/app/interfaces/filter";
import clsx from "clsx";
import { parseArrayString } from "@/app/utils/helper";
import { getSchemes } from "../main-chat";
// Type for scheme from search results
export type SearchResScheme = {
  schemeId: string;
  schemeType: string;
  schemeName: string;
  agency: string;
  description: string;
  targetAudience: string;
  scrapedText: string;
  benefits: string;
  link: string;
  image: string;
  searchBooster: string;
  query: string;
  similarity: number;
  quintile: number;
  planningArea: string | string[];
  summary: string;
};

interface SchemesListProps {
  isLoadingSchemes: boolean;
  filterObj: FilterObjType;
  setFilterObj: Dispatch<SetStateAction<FilterObjType>>;
  nextCursor: string;
  setNextCursor: (val: string) => void;
  selectedLocations: Set<string>;
  setSelectedLocations: Dispatch<SetStateAction<Set<string>>>;
  selectedAgencies: Set<string>;
  setSelectedAgencies: Dispatch<SetStateAction<Set<string>>>;
  resetFilters: () => void;
}

export default function SchemesList({
  isLoadingSchemes,
  filterObj,
  setFilterObj,
  selectedLocations,
  setSelectedLocations,
  selectedAgencies,
  setSelectedAgencies,
  resetFilters,
}: SchemesListProps) {
  const listTopRef = useRef<HTMLDivElement>(null);
  const listBottomRef = useRef<HTMLDivElement>(null);
  const bottomReached = useInView(listBottomRef);
  const [isLoadingMoreSchemes, setIsLoadingMoreSchemes] = useState(false);
  const { schemes, setSchemes, sessionId, totalCount, userQuery, nextCursor, setNextCursor } = useChat();

  // Compute filtered schemes once per render
  const filteredSchemes = useMemo(
    () =>
      schemes.filter((scheme) => {
        if (filterObj.planningArea && filterObj.planningArea.size > 0) {
          if (
            !scheme.planningArea ||
            filterObj.planningArea.intersection(
              new Set(parseArrayString(scheme.planningArea))
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
    [schemes, filterObj]
  );

  // scroll to top when sessionId changes
  useEffect(() => {
    if (listTopRef.current) {
      listTopRef.current.scrollIntoView()
    }
  }, [sessionId])

  // load more schemes when bottom of list reached
  useEffect(() => {
    if (bottomReached && nextCursor) {
      loadMoreSchemes()
    }
  }, [bottomReached]);

  const loadMoreSchemes = () => {
    setIsLoadingMoreSchemes(true)
    getSchemes(userQuery, nextCursor).then(res => {
      const {schemesRes, nextCursor : newCursor} = res
      if (schemesRes) {
        setSchemes((prevSchemes) => [...prevSchemes, ...schemesRes])
      }
      if (nextCursor) {
        setNextCursor(newCursor)
      }
    })
    setIsLoadingMoreSchemes(false)
  }

  return (
    <div className="overflow-y-hidden flex flex-col relative">
      <div className="flex gap-2 justify-between">
        <div className="flex flex-col gap-1 shrink-0 p-2">
          <p className="text-base font-semibold">Search Results</p>
          <p className="text-xs text-slate-500">
            Showing {filteredSchemes.length} of {totalCount} schemes
          </p>
        </div>
        <SchemesFilter
          schemes={schemes}
          setFilterObj={setFilterObj}
          selectedLocations={selectedLocations}
          setSelectedLocations={setSelectedLocations}
          selectedAgencies={selectedAgencies}
          setSelectedAgencies={setSelectedAgencies}
          resetFilters={resetFilters}
        />
      </div>

      <Spacer y={3} />

      <div
        className={clsx(
          "p-2 overflow-x-hidden overflow-y-auto",
          "grid grid-cols-1 lg:grid-cols-2 gap-2",
        )}
      >
        <div
          className={clsx(
            "p-2 flex justify-center",
            "col-span-1 lg:col-span-2"
          )}
          ref={listTopRef}
        >
        </div>
        {filteredSchemes.map((scheme) => (
          <SchemeCard key={scheme.schemeId} scheme={scheme} />
        ))}
        <div
          className={clsx(
            "p-2 flex justify-center",
            "col-span-1 lg:col-span-2"
          )}
          ref={listBottomRef}
        >
          {isLoadingMoreSchemes && <Spinner />}
        </div>
      </div>
      {isLoadingSchemes && (
        <div
          className={clsx(
            "w-full h-full p-2 z-50",
            "absolute bg-white/70",
            "flex justify-center items-center"
          )}
        >
          <Spinner size="lg" />
        </div>
      )}
    </div>
  );
}
