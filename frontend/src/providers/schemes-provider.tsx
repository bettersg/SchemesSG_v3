"use client";

import { Scheme } from "@/types/types";
import React, { createContext, ReactNode, useContext, useState } from "react";

type SchemesContextType = {
  sessionId: string;
  setSessionId: React.Dispatch<React.SetStateAction<string>>;
  totalCount: number;
  setTotalCount: React.Dispatch<React.SetStateAction<number>>;
  nextCursor: string;
  setNextCursor: React.Dispatch<React.SetStateAction<string>>;
  schemes: Scheme[];
  setSchemes: React.Dispatch<React.SetStateAction<Scheme[]>>;
  userQuery: string;
  setUserQuery: React.Dispatch<React.SetStateAction<string>>;
};

const SchemesContext = createContext<SchemesContextType | undefined>(undefined);

export const SchemesProvider = ({ children }: { children: ReactNode }) => {
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [totalCount, setTotalCount] = useState(0);
  const [nextCursor, setNextCursor] = useState("");
  const [userQuery, setUserQuery] = useState("");

  return (
    <SchemesContext.Provider
      value={{
        schemes,
        setSchemes,
        sessionId,
        setSessionId,
        totalCount,
        setTotalCount,
        nextCursor,
        setNextCursor,
        userQuery,
        setUserQuery,
      }}
    >
      {children}
    </SchemesContext.Provider>
  );
};

export const useSchemes = (): SchemesContextType => {
  const context = useContext(SchemesContext);
  if (!context) {
    throw new Error("useSchemes must be used within a SchemesProvider");
  }
  return context;
};
