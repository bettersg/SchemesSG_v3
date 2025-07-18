"use client";
import MiniChatBar from "@/components/chat-bar/mini-chat-bar";
import MainChat from "@/components/main-chat";
import QueryGenerator from "@/components/query-generator/query-generator";
import SchemesList from "@/components/schemes/schemes-list";
import SearchBar from "@/components/search-bar";
import UserQuery from "@/components/user-query";
import { useState } from "react";
import { useChat } from "./providers";
import Image from "next/image";
import backgroundImageOne from "@/assets/bg1.png";
import backgroundImageTwo from "@/assets/bg2.png";
import Partners from "@/components/partners";
import { FilterObjType } from "./interfaces/filter";
import clsx from "clsx";

export default function Home() {
  const { schemes, setSchemes, sessionId, setSessionId } = useChat();
  const [isExpanded, setIsExpanded] = useState(false);
  const [nextCursor, setNextCursor] = useState("");
  const [selectedSupportProvided, setSelectedSupportProvided] = useState<
    string | null
  >(null);
  const [selectedForWho, setSelectedForWho] = useState<string | null>(null);
  const [selectedSchemeType, setSelectedSchemeType] = useState<string | null>(
    null
  );
  const [filterObj, setFilterObj] = useState<FilterObjType>({});
  // const [selectedOrganisation, setSelectedOrganisation] = useState<string | null>(null);

  // LIFTED filter state
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
              <UserQuery resetFilters={resetFilters} />
            </div>
            <div className="hidden md:flex">
              <MainChat
                sessionId={sessionId}
                filterObj={filterObj}
                resetFilters={resetFilters}
              />
            </div>
            <SchemesList
              schemes={schemes}
              setSchemes={setSchemes}
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
              {isExpanded && <MainChat
                sessionId={sessionId}
                filterObj={filterObj}
                resetFilters={resetFilters}
                setIsExpanded={setIsExpanded}
              />}
            </div>
            <MiniChatBar
              onExpand={() => setIsExpanded(true)}
              isExpanded={isExpanded}
            />
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center">
          <div className="max-w-[35rem] p-4">
            {/* Desktop*/}
            <div className="hidden md:block">
              <h1 className="text-center text-4xl font-bold">
                <span className="text-schemes-darkblue">
                  Welcome to Schemes
                </span>
                <span className="text-schemes-blue">SG</span>
              </h1>
              <p className="text-schemes-darkblue text-center mt-6 text-lg">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
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
          <div className="flex flex-col justify-center items-center my-8">
            <QueryGenerator
              // setSessionId={setSessionId}
              setSelectedSupportProvided={setSelectedSupportProvided}
              setSelectedForWho={setSelectedForWho}
              // setSelectedOrganisation={setSelectedOrganisation}
              setSelectedSchemeType={setSelectedSchemeType}
              onSendQuery={() => {}}
            />
          </div>
          <SearchBar
            setSessionId={setSessionId}
            selectedSupportProvided={selectedSupportProvided}
            selectedForWho={selectedForWho}
            // selectedOrganisation={selectedOrganisation}
            selectedSchemeType={selectedSchemeType}
            setSelectedSupportProvided={setSelectedSupportProvided}
            setSelectedForWho={setSelectedForWho}
            setSelectedSchemeType={setSelectedSchemeType}
          />
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
