import { useChat } from "@/app/providers";
import { Button, Spinner, Textarea } from "@heroui/react";
import { useEffect, useState } from "react";
import { SearchIcon } from "../assets/icons/search-icon";
import { getSchemes } from "./main-chat";


interface SearchBarProps {
  selectedSupportProvided: string | null;
  selectedForWho: string | null;
  // selectedOrganisation: string | null;
  selectedSchemeType: string | null;
  setSelectedSupportProvided: React.Dispatch<
    React.SetStateAction<string | null>
  >;
  setSelectedForWho: React.Dispatch<React.SetStateAction<string | null>>;
  setSelectedSchemeType: React.Dispatch<React.SetStateAction<string | null>>;
  onSendQuery?: () => void;
}
export default function SearchBar({
  selectedSupportProvided,
  selectedForWho,
  // selectedOrganisation,
  selectedSchemeType,
  setSelectedSupportProvided,
  setSelectedForWho,
  setSelectedSchemeType,
}: SearchBarProps) {
  const { setMessages, userQuery, setUserQuery, setSchemes, setSessionId, setTotalCount, setNextCursor } = useChat();
  const [isBotResponseGenerating, setIsBotResponseGenerating] =
    useState<boolean>(false);

  useEffect(() => {
    let query = "I am";

    // Handle ForWho
    if (selectedForWho) {
      query += ` ${selectedForWho}`;
    }

    if (selectedSchemeType || selectedSupportProvided) {
      // Add "looking for" after ForWho or at start
      query += " looking for";
    }
    // Handle SchemeType
    if (selectedSchemeType) {
      query += ` ${selectedSchemeType}`;
    } else if (selectedSupportProvided) {
      // If no SchemeType but has SupportProvided, add "scheme"
      query += " scheme";
    }

    // Handle SupportProvided
    if (selectedSupportProvided) {
      query += ` that offers ${selectedSupportProvided}`;
    }

    // Default to empty if it's just the basic phrase
    setUserQuery(query === "I am" ? "" : query);
  }, [
    selectedForWho,
    selectedSchemeType,
    selectedSupportProvided,
    setUserQuery,
  ]);

  const handleSend = async () => {
    if (userQuery.trim()) {
      setIsBotResponseGenerating(true);
      const { schemesRes, sessionId, totalCount, nextCursor } = await getSchemes(userQuery);
      setTotalCount(totalCount)
      setNextCursor(nextCursor)
      setUserQuery(userQuery);
      setIsBotResponseGenerating(false);
      
      // Always set sessionId if it exists, regardless of results
      if (sessionId !== "") {
        setSessionId(sessionId);
        setMessages([
          {
            type: "user",
            text: userQuery,
          },
        ]);
      }
      
      // Set schemes if we have results
      if (schemesRes.length > 0) {
        setSchemes(schemesRes);
      } else {
        // Clear schemes if no results but keep sessionId for chat
        setSchemes([]);
      }

      // Reset the filters
      setSelectedSupportProvided(null);
      setSelectedForWho(null);
      setSelectedSchemeType(null);
    }
  };

  return (
    <>
      <Textarea
        value={userQuery}
        onChange={(e) => setUserQuery(e.target.value)}
        onKeyDown={async (e) => {
          if (e.key === "Enter" && !isBotResponseGenerating) {
            e.preventDefault();
            await handleSend();
          }
        }}
        className="max-w-[35rem] mx-auto"
        classNames={{
          input: "placeholder:italic placeholder:text-black/20",
        }}
        type="text"
        size="md"
        radius="lg"
        color="primary"
        label="How can we help?"
        labelPlacement="outside"
        description="Please avoid providing identifiable information."
        placeholder="E.g. I am a cancer patient in need of financial assistance and food support."
        endContent={
          <div className="flex items-end gap-2 h-full">
            {isBotResponseGenerating ? (
              <>
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  Finding schemes...
                </span>
                <Spinner size="sm" className="mt-auto" />
              </>
            ) : (
              <Button
                color="primary"
                isIconOnly
                size="sm"
                radius="full"
                onPress={async () => await handleSend()}
                className="mt-auto"
              >
                <SearchIcon size={16} />
              </Button>
            )}
          </div>
        }
      />
    </>
  );
}
