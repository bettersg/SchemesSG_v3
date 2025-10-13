"use client";
import MiniChatBar from "@/components/chat-bar/mini-chat-bar";
import MainChat from "@/components/main-chat";
import SchemesList from "@/components/schemes/schemes-list";
import SearchBar from "@/components/search-bar";
import UserQuery from "@/components/user-query";
import { useRef, useState } from "react";
import { useChat } from "./providers";
import Image from "next/image";
import backgroundImageOne from "@/assets/bg1.png";
import backgroundImageTwo from "@/assets/bg2.png";
import Partners from "@/components/partners";
import { FilterObjType } from "./interfaces/filter";
import clsx from "clsx";
import QueryPrompts from "@/components/query-prompts";

export default function Home() {
  const { schemes } = useChat();
  const [isLoadingSchemes, setIsLoadingSchemes] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [nextCursor, setNextCursor] = useState("");

  const searchbarRef = useRef<HTMLTextAreaElement | null>(null);
  const focusSearchbar = () => {
    if (searchbarRef.current) {
      searchbarRef.current.focus();
    }
  };

  // filter states
  const [filterObj, setFilterObj] = useState<FilterObjType>({});
  const [selectedLocations, setSelectedLocations] = useState(new Set(""));
  const [selectedAgencies, setSelectedAgencies] = useState(new Set(""));
  const resetFilters = () => {
    setSelectedLocations(new Set(""));
    setSelectedAgencies(new Set(""));
    setFilterObj({});
  };

  return (
    <main
      className={clsx(
        "max-w-[1500px] h-full",
        "relative z-10",
        "flex flex-col items-center",
        "p-4 sm:py-2 md:px-8 lg:px-16",
        "xl:mx-auto"
      )}
    >
      {schemes.length > 0 ? (
        <>
          {/* Desktop Layout */}
          <div
            className={clsx(
              "overflow-hidden",
              "max-md:flex flex-col h-full",
              "md:grid gap-2 grid-rows-1 grid-cols-2 lg:grid-cols-[2fr_3fr]"
            )}
          >
            <div className="flex md:hidden">
              <UserQuery
                resetFilters={resetFilters}
                setIsLoadingSchemes={setIsLoadingSchemes}
              />
            </div>
            <div className="hidden md:flex">
              <MainChat
                filterObj={filterObj}
                resetFilters={resetFilters}
                setIsLoadingSchemes={setIsLoadingSchemes}
              />
            </div>
            <SchemesList
              isLoadingSchemes={isLoadingSchemes}
              filterObj={filterObj}
              setFilterObj={setFilterObj}
              nextCursor={nextCursor}
              setNextCursor={setNextCursor}
              selectedLocations={selectedLocations}
              setSelectedLocations={setSelectedLocations}
              selectedAgencies={selectedAgencies}
              setSelectedAgencies={setSelectedAgencies}
              resetFilters={resetFilters}
            />
          </div>

          {/* Mobile Layout */}
          <div
            className={`md:hidden flex fixed bottom-0 left-0 right-0 bg-none transition-all duration-300 ease-in-out z-50
            ${isExpanded ? "h-full" : "h-0"}`}
          >
            <div
              className={clsx(
                "w-full h-full",
                "transition-opacity duration-300 pt-12",
                !isExpanded && "pointer-events-none"
              )}
            >
              {isExpanded && (
                <MainChat
                  filterObj={filterObj}
                  resetFilters={resetFilters}
                  setIsExpanded={setIsExpanded}
                  setIsLoadingSchemes={setIsLoadingSchemes}
                />
              )}
            </div>
            <MiniChatBar
              onExpand={() => setIsExpanded(true)}
              isExpanded={isExpanded}
            />
          </div>
        </>
      ) : (
        <div className="max-w-[35rem] flex flex-col items-center gap-4">
          <div className="p-4">
            {/* Desktop*/}
            <div className="hidden md:block">
              <h1 className="text-center text-4xl font-bold">
                <span className="text-schemes-darkblue">
                  Welcome to Schemes
                </span>
                <span className="text-schemes-blue">SG</span>
              </h1>
              <p className="text-schemes-darkblue text-center mt-6 text-lg">
                An AI-supported search engine for public social assistance
                schemes in Singapore.
              </p>
            </div>

            {/* Mobile*/}
            <div className="block md:hidden">
              <h1 className="text-[32px] font-bold leading-tight">
                <div className="text-schemes-darkblue text-center">
                  Welcome to
                </div>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-schemes-darkblue">Schemes</span>
                  <span className="text-schemes-blue">SG</span>
                </div>
              </h1>
              <p className="text-schemes-darkblue mt-4 text-center leading-snug text-base">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
              </p>
            </div>
          </div>
          <SearchBar searchbarRef={searchbarRef} />
          <QueryPrompts focusSearchbar={focusSearchbar} />
          <Partners />
          <Image
            src={backgroundImageOne}
            alt="background image one"
            className="absolute w-[35%] top-[10%] left-0 -z-10"
            unoptimized
            priority
          />
          <Image
            src={backgroundImageTwo}
            alt="background image two"
            className="absolute w-[35%] top-0 right-0 -z-10"
            unoptimized
            priority
          />
        </div>
      )}
    </main>
  );
}
