import { RawSchemeData, SearchResponse } from "@/app/interfaces/schemes";
import { useChat } from "@/app/providers";
import { fetchWithAuth } from "@/app/utils/api";
import { Button, Spinner, Textarea } from "@heroui/react";
import { useEffect, useState } from "react";
import { SearchIcon } from "../assets/icons/search-icon";
import { SearchResScheme } from "./schemes/schemes-list";

export const mapToScheme = (rawData: RawSchemeData): SearchResScheme => {
  return {
    schemeType: rawData["scheme_type"] || rawData["Scheme Type"] || "",
    schemeName: rawData["scheme"] || rawData["Scheme"] || "",
    targetAudience: rawData["who_is_it_for"] || rawData["Who's it for"] || "",
    agency: rawData["agency"] || rawData["Agency"] || "",
    description: rawData["description"] || rawData["Description"] || "",
    scrapedText: rawData["scraped_text"] || "",
    benefits: rawData["what_it_gives"] || rawData["What it gives"] || "",
    link: rawData["link"] || rawData["Link"] || "",
    image: rawData["image"] || rawData["Image"] || "",
    searchBooster:
      rawData["search_booster"] || rawData["search_booster(WL)"] || "",
    schemeId: rawData["scheme_id"] || "",
    query: rawData["query"] || "",
    similarity: rawData["Similarity"] || 0,
    quintile: rawData["Quintile"] || 0,
    planningArea: rawData["planning_area"] || "",
    summary: rawData["summary"] || "",
  };
};

export const getSchemes = async (userQuery: string) => {
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;

    const requestBody = {
      query: userQuery,
      top_k: 50,
      similarity_threshold: 0,
    };

    try {
      const response = await fetchWithAuth(url, {
        method: "POST",
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const res = (await response.json()) as SearchResponse;
      console.log("Search response:", res); // Debug

      const sessionId: string = res["sessionID"] || "";

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
        return { schemesRes, sessionId };
      } else {
        console.error("Unexpected response format:", res);
        return { schemesRes: [], sessionId };
      }
    } catch (error) {
      console.error("Error making POST request:", error);
      return { schemesRes: [], sessionId: "" };
    }
  };

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
  const { setMessages, userQuery, setUserQuery, setSchemes, setSessionId } = useChat();
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
      const { schemesRes, sessionId } = await getSchemes(userQuery);
      setIsBotResponseGenerating(false);
      if (schemesRes.length > 0 && sessionId !== "") {
        schemesRes && setSchemes(schemesRes);
        setSessionId(sessionId);
        setMessages([
          {
            type: "user",
            text: userQuery,
          },
        ]);
        setUserQuery("");
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
