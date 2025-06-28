"use client";

import { Spacer, Spinner } from "@heroui/react";
import SchemeCard from "./scheme-card";
import SchemesFilter from "./schemes-filter";
import { Dispatch, SetStateAction, useEffect, useRef, useState, useMemo } from "react";
import { useInView } from "framer-motion";
import { useChat } from "@/app/providers";
import { fetchWithAuth } from "@/app/utils/api";
import { SearchResponse } from "@/app/interfaces/schemes";
import { mapToScheme } from "../search-bar";
import { FilterObjType } from "@/app/interfaces/filter";
import clsx from "clsx";
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
  planningArea: string;
  summary: string;
};

interface SchemesListProps {
  schemes: SearchResScheme[];
  setSchemes: Dispatch<SetStateAction<SearchResScheme[]>>;
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
  schemes,
  setSchemes,
  filterObj,
  setFilterObj,
  nextCursor,
  setNextCursor,
  selectedLocations,
  setSelectedLocations,
  selectedAgencies,
  setSelectedAgencies,
  resetFilters,
}: SchemesListProps) {
  const listBottomRef = useRef(null);
  const bottomReached = useInView(listBottomRef);
  const [isLoadingSchemes, setIsLoadingSchemes] = useState(false);
  const { userQuery } = useChat();

  // Compute filtered schemes once per render
  const filteredSchemes = useMemo(
    () =>
      schemes.filter((scheme) => {
        if (filterObj.planningArea && filterObj.planningArea.size > 0) {
          if (!scheme.planningArea || !filterObj.planningArea.has(scheme.planningArea)) {
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

  useEffect(() => {
    if (bottomReached && nextCursor) {
      console.log('loading');
      loadMoreSchemes();
    }
  });

  const loadMoreSchemes = async () => {
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;
    const requestBody = {
      query: userQuery,
      limit: 20,
      top_k: 50,
      similarity_threshold: 0,
      cursor: nextCursor,
    };
    try {
      setIsLoadingSchemes(true);
      const response = await fetchWithAuth(url, {
        method: "POST",
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const res = await response.json() as SearchResponse;
      console.log("Search response:", res); // Debug

      setIsLoadingSchemes(false)

      // Check if there is more data to be paginated
      if (res.has_more && res.next_cursor) {
        setNextCursor(res.has_more ? res.next_cursor : '')
      }

      // Check if data exists in the response
      if (res.data) {
        let schemesData;

        // Handle both array and single object responses
        if (Array.isArray(res.data)) {
          schemesData = res.data;
        } else {
          // If it's a single object, convert to array
          schemesData = [res.data];
        }

        const schemesRes: SearchResScheme[] = schemesData.map(mapToScheme);
        console.log("Mapped schemes:", schemesRes); // Debug
        setSchemes(prevSchemes => [...prevSchemes, ...schemesRes])
      }
    } catch (error) {
      console.error("Error making POST request:", error);
      setIsLoadingSchemes(false);
      return { schemesRes: [], sessionId: "" };
    }
  };
  return (
    <div className="h-full flex flex-col">
      <div className="flex gap-2 justify-between">
        <div className="flex flex-col gap-1 shrink-0 p-2">
          <p className="text-base font-semibold">Search Results</p>
          <p className="text-xs text-slate-500">
            Showing {filteredSchemes.length} schemes
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
          "p-2",
          "gap-2 grid grid-cols-1 lg:grid-cols-2",
          "overflow-x-hidden overflow-y-auto",
        )}
      >
        {filteredSchemes.map((scheme) => (
          <SchemeCard key={scheme.schemeId} scheme={scheme} />
        ))}
      </div>

      <div ref={listBottomRef}>
        {isLoadingSchemes && <Spinner />}
      </div>
    </div>
  );
}
