"use client";
import { useState } from "react";
import { useChat } from "../providers";
import { FilterObjType } from "../types/types";
import dynamic from "next/dynamic";
import ChatPage from "@/components/chat/chat-page";
import ChatLanding from "@/components/chat/chat-landing";

export default function Home() {
  const { messages } = useChat();
//   const [isLoadingSchemes, setIsLoadingSchemes] = useState(false);
//   const [filterObj, setFilterObj] = useState<FilterObjType>({});
//   const [selectedLocations, setSelectedLocations] = useState(new Set(""));
//   const [selectedAgencies, setSelectedAgencies] = useState(new Set(""));

//   const resetFilters = () => {
//     setSelectedLocations(new Set(""));
//     setSelectedAgencies(new Set(""));
//     setFilterObj({});
//   };

  if (messages.length > 0) {
    return (
      <ChatPage
        // filterObj={filterObj}
        // setFilterObj={setFilterObj}
        // selectedLocations={selectedLocations}
        // setSelectedLocations={setSelectedLocations}
        // selectedAgencies={selectedAgencies}
        // setSelectedAgencies={setSelectedAgencies}
        // resetFilters={resetFilters}
        // isLoadingSchemes={isLoadingSchemes}
        // setIsLoadingSchemes={setIsLoadingSchemes}
      />
    );
  }

  return <ChatLanding />;
}
