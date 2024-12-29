import { RawSchemeData } from "@/app/interfaces/schemes";
import { useChat } from "@/app/providers";
import { Button, Spinner, Textarea } from "@nextui-org/react";
import { useEffect, useState } from "react";
import { SearchIcon } from "../../assets/icons/search-icon";
import { SearchResScheme } from "../schemes/schemes-list";
import classes from "./search-bar.module.css";

interface SearchBarProps {
  setSessionId: (val: string) => void;
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
  setSessionId,
  selectedSupportProvided,
  selectedForWho,
  // selectedOrganisation,
  selectedSchemeType,
  setSelectedSupportProvided,
  setSelectedForWho,
  setSelectedSchemeType,
}: SearchBarProps) {
  const { setMessages, userQuery, setUserQuery, setSchemes } = useChat();
  // const [userInput, setUserInput] = useState("");
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
  }, [selectedForWho, selectedSchemeType, selectedSupportProvided]);

  const handleUserQuery = (input: string) => {
    setMessages([
      {
        type: "user",
        text: input,
      },
    ]);
    // Make sure input is a string
    if (typeof input === "string") {
      setUserQuery(input);
    }
    setUserQuery("");
  };

  const mapToScheme = (rawData: RawSchemeData): SearchResScheme => {
    return {
      schemeType: rawData["Scheme Type"] || "",
      schemeName: rawData["Scheme"] || "",
      targetAudience: rawData["Who's it for"] || "",
      agency: rawData["Agency"] || "",
      description: rawData["Description"] || "",
      scrapedText: rawData["scraped_text"] || "",
      benefits: rawData["What it gives"] || "",
      link: rawData["Link"] || "",
      image: rawData["Image"] || "",
      searchBooster: rawData["search_booster(WL)"] || "",
      schemeId: rawData["scheme_id"] || "",
      query: rawData["query"] || "",
      similarity: rawData["Similarity"] || 0,
      quintile: rawData["Quintile"] || 0,
    };
  };

  const getSchemes = async () => {
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;

    const requestBody = {
      query: userQuery,
      top_k: 20,
      similarity_threshold: 0,
    };

    try {
      setIsBotResponseGenerating(true);
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const res = await response.json();
      const sessionId: string = res["sessionID"];
      setIsBotResponseGenerating(false);
      const schemesRes: SearchResScheme[] = res.data.map(mapToScheme);
      return { schemesRes, sessionId };
    } catch (error) {
      console.error("Error making POST request:", error);
      setIsBotResponseGenerating(false);
      return { schemesRes: [], sessionId: "" };
    }
  };

  const handleSend = async () => {
    if (userQuery.trim()) {
      const { schemesRes, sessionId } = await getSchemes();
      if (schemesRes.length > 0 && sessionId !== "") {
        schemesRes && setSchemes(schemesRes);
        setSessionId(sessionId);
        handleUserQuery(userQuery);
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
        className={classes.searchBar}
        type="text"
        size="md"
        radius="lg"
        color="primary"
        label="How can we help?"
        labelPlacement="outside"
        description="Please avoid providing identifiable information."
        placeholder="E.g. I am a cancer patient in need of financial assistance and food support."
        endContent={
          isBotResponseGenerating ? (
            <Spinner className={classes.endContent} size="sm" />
          ) : (
            <Button
              className={classes.endContent}
              isIconOnly
              size="sm"
              radius="full"
              onClick={async () => await handleSend()}
            >
              <SearchIcon />
            </Button>
          )
        }
      />
    </>
  );
}
