"use client";

import { useChat } from "@/app/providers";
import { fetchWithAuth } from "@/app/utils/api";
import ChatBar from "@/components/chat-bar/chat-bar";
import ChatList from "@/components/chat-list";
import { Button, Spacer } from "@heroui/react";
import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react";
import UserQuery from "./user-query";
import { FilterObjType } from "@/app/interfaces/filter";
import clsx from "clsx";
import { MinimizeIcon } from "@/assets/icons/minimize-icon";
import { SearchResScheme } from "./schemes/schemes-list";
import { RawSchemeData, SearchResponse } from "@/app/interfaces/schemes";

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

export const getSchemes = async (
  userQuery: string,
  nextCursor = ""
): Promise<{
  schemesRes: SearchResScheme[];
  sessionId: string;
  totalCount: number;
  nextCursor: string;
}> => {
  const url = `${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes_search`;

  const requestBody = {
    query: userQuery,
    limit: 20,
    top_k: 50,
    similarity_threshold: 0,
    cursor: nextCursor,
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

    const sessionId: string = res.sessionID || "";
    const totalCount: number = res.total_count || 0;
    const hasMore: boolean = res.has_more || false;
    const nextCursor: string = res.next_cursor && hasMore ? res.next_cursor : '';

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
      return { schemesRes, sessionId, totalCount, nextCursor };
    } else {
      console.error("Unexpected response format:", res);
      return { schemesRes: [], sessionId, totalCount, nextCursor };
    }
  } catch (error) {
    console.error("Error making POST request:", error);
    return { schemesRes: [], sessionId: "", totalCount: 0, nextCursor: "" };
  }
};

type MainChatProps = {
  filterObj: FilterObjType;
  resetFilters: () => void;
  setIsExpanded?: Dispatch<SetStateAction<boolean>>;
  setIsLoadingSchemes: (value: boolean) => void;
};

export default function MainChat({
  filterObj,
  resetFilters,
  setIsExpanded,
  setIsLoadingSchemes,
}: MainChatProps) {
  const { messages, setMessages, sessionId } = useChat();
  const [userInput, setUserInput] = useState("");
  const [isBotResponseGenerating, setIsBotResponseGenerating] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");
  const scrollableDivRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Append bot message only once
    if (
      messages.length === 1 // User message exists
    ) {
      setMessages([
        ...messages, // Existing user messages
        {
          type: "bot",
          text: "You can see the search results on the right. Please ask me any further questions about the schemes.",
        },
      ]);
    }
  }, [setMessages, messages]); // Minimal dependency array

  useEffect(() => {
    handleScrollToBottom();
  }, [messages]);

  const handleUserInput = async (input: string) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "user", text: input },
    ]);

    await fetchBotResponse(input);
  };

  const handleBotResponse = (response: string) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "bot", text: response },
    ]);
  };

  const fetchBotResponse = async (userMessage: string) => {
    setIsBotResponseGenerating(true);
    setCurrentStreamingMessage("");
    try {
      const bodyParams: { [key: string]: string | string[] | boolean } = {
        message: userMessage,
        sessionID: sessionId,
        stream: true,
      };
      if (filterObj.planningArea) {
        bodyParams.planning_area = Array.from(filterObj.planningArea);
      }
      if (filterObj.agency) {
        bodyParams.agency = Array.from(filterObj.agency);
      }
      const response = await fetchWithAuth(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/chat_message`,
        {
          method: "POST",
          body: JSON.stringify(bodyParams),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch bot response");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No reader available");
      }

      let fullMessage = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        lines.forEach((line) => {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              fullMessage += data.chunk;
              setCurrentStreamingMessage(fullMessage);
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        });
      }
      handleBotResponse(fullMessage);
    } catch (error) {
      console.error("Error fetching bot response:", error);
      handleBotResponse("Sorry, something went wrong. Please try again.");
    } finally {
      setIsBotResponseGenerating(false);
      setCurrentStreamingMessage("");
    }
  };

  const handleScrollToBottom = () => {
    if (scrollableDivRef.current) {
      scrollableDivRef.current.scrollTo({
        top: scrollableDivRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  return (
    <>
      <div
        className={clsx(
          "w-full h-full",
          "flex flex-col",
          "bg-schemes-lightgray rounded-2xl",
          "mx-auto px-8 py-2"
        )}
      >
        <UserQuery
          resetFilters={resetFilters}
          setIsLoadingSchemes={setIsLoadingSchemes}
        />
        <ChatList
          messages={messages}
          streamingMessage={currentStreamingMessage}
          scrollableDivRef={scrollableDivRef}
        />
        <div
          className={clsx(
            "flex justify-between items-center",
            "bg-transparent border-b",
            "mt-auto border-gray-100"
          )}
        >
          {setIsExpanded && (
            <Button
              isIconOnly
              color="primary"
              variant="solid"
              onPress={() => setIsExpanded(false)}
              className="z-10 ml-auto"
            >
              <MinimizeIcon size={16} />
            </Button>
          )}
        </div>
        <Spacer y={4} />
        <ChatBar
          userInput={userInput}
          setUserInput={setUserInput}
          handleUserInput={handleUserInput}
          isBotResponseGenerating={isBotResponseGenerating}
        />
      </div>
    </>
  );
}
