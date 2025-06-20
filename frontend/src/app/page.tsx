"use client";
import { ExpandIcon } from "@/assets/icons/expand-icon";
import MiniChatBar from "@/components/chat-bar/mini-chat-bar";
import MainChat from "@/components/main-chat/main-chat";
import QueryGenerator from "@/components/query-generator/query-generator";
import SchemesList from "@/components/schemes/schemes-list";
import SearchBar from "@/components/search-bar/search-bar";
import UserQuery from "@/components/user-query/user-query";
import { Button } from "@nextui-org/react";
import { useState } from "react";
import classes from "../components/main-layout/main-layout.module.css";
import { useChat } from "./providers";
import Image from "next/image";
import backgroundImageOne from "@/assets/bg1.png";
import backgroundImageTwo from "@/assets/bg2.png";
import Partners from "@/components/partners/partners";
import { FilterObjType } from "./interfaces/filter";

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
  const [filterObj, setFilterObj] = useState<FilterObjType>({})
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
    <main className={classes.homePage}>
      {schemes.length > 0 ? (
        <>
          {/* Desktop Layout */}
          <div className={classes.mainLayout}>
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
              className={`w-full h-full transition-opacity duration-300 pt-12
              ${isExpanded ? "opacity-100" : "opacity-0 pointer-events-none"}`}
            >
              <MainChat
                sessionId={sessionId}
                filterObj={filterObj}
                resetFilters={resetFilters}
              />
            </div>
            <div
              className={`absolute left-0 right-0 flex justify-between items-center p-2 bg-transparent border-b
              ${isExpanded ? "border-gray-100" : "border-none"} bottom-20`}
            >
              {/* {isExpanded && (
                <span className="text-sm font-medium px-2">Chat</span>
              )} */}
              <Button
                isIconOnly
                variant="light"
                onClick={() => setIsExpanded(!isExpanded)}
                className="z-10 ml-auto"
              >
                {isExpanded ? <ExpandIcon /> : null}
              </Button>
            </div>
            <MiniChatBar
              onExpand={() => setIsExpanded(true)}
              isExpanded={isExpanded}
            />
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full">
          <div className={classes.welcomeMsg}>
            {/* Desktop*/}
            <div className="hidden md:block">
              <h1 className="text-center text-4xl font-bold">
                <span className="text-[#171347]">Welcome to Schemes</span>
                <span className="text-[#008AFF]">SG</span>
              </h1>
              <p className="text-[#171347] text-center mt-6 text-lg">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
              </p>
            </div>

            {/* Mobile*/}
            <div className="block md:hidden">
              <h1 className="text-[32px] font-bold leading-tight">
                <div className="text-[#171347] text-center">Welcome to</div>
                <div className="flex items-center justify-center gap-2">
                  <span className="text-[#171347]">Schemes</span>
                  <span className="text-[#008AFF]">SG</span>
                </div>
              </h1>
              <p className="text-[#171347] mt-4 text-center leading-snug text-base">
                This is an AI-supported search engine for public social
                assistance schemes in Singapore.
              </p>
            </div>
          </div>
          <div className={classes.centered}>
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
            className={classes.bgOne}
            unoptimized
            priority
          />
          <Image
            src={backgroundImageTwo}
            alt="background image two"
            className={classes.bgTwo}
            unoptimized
            priority
          />
        </div>
      )}
    </main>
  );
}
