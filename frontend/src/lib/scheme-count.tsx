"use client";

import { createContext, useContext, type ReactNode } from "react";
import { FALLBACK_SCHEME_COUNT } from "@/lib/seo";

// The catalogue size shown in landing copy ("over 700 schemes"). Pages that
// fetch it provide it; anywhere else, including tests, gets the fallback.
const SchemeCountContext = createContext(FALLBACK_SCHEME_COUNT);

export function SchemeCountProvider({
  count,
  children,
}: {
  count: number;
  children: ReactNode;
}) {
  return (
    <SchemeCountContext.Provider value={count}>
      {children}
    </SchemeCountContext.Provider>
  );
}

/** The count formatted for copy, e.g. "1,200". */
export function useSchemeCount() {
  return useContext(SchemeCountContext).toLocaleString("en-SG");
}
