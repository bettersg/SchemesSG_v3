"use client";

import { useChat } from "@/app/providers";
import { fetchWithAuth } from "@/app/utils/api";
import ChatBar from "@/components/chat-bar/chat-bar";
import ChatList from "@/components/chat-list";
import { Spacer } from "@nextui-org/react";
import { useEffect, useRef, useState } from "react";
import UserQuery from "./user-query";
import { FilterObjType } from "@/app/interfaces/filter";
import clsx from "clsx";

type MainChatProps = {
  sessionId: string;
  filterObj: FilterObjType;
  resetFilters: () => void;
};

export default function MainChat({
  sessionId,
  filterObj,
  resetFilters,
}: MainChatProps) {
  const { messages, setMessages } = useChat();
  const [userInput, setUserInput] = useState("");
  const [isBotResponseGenerating, setIsBotResponseGenerating] =
    useState<boolean>(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");
  const scrollableDivRef = useRef<HTMLDivElement>(null);

  const [botMessageAdded, setBotMessageAdded] = useState(false);

  useEffect(() => {
    const storedQuery = localStorage.getItem("userQuery");
    const storedMessages = localStorage.getItem("userMessages");

    // Parse storedMessages safely
    const parsedMessages =
      storedMessages && storedMessages !== "[]"
        ? JSON.parse(storedMessages)
        : [];

    // Append bot message only once
    if (
      storedQuery &&
      parsedMessages.length === 0 && // No stored messages
      !botMessageAdded && // Bot message has not been added
      messages.length === 1 // User message exists
    ) {
      setMessages([
        ...messages, // Existing user messages
        {
          type: "bot",
          text: "You can see the search results on the right. Please ask me any further questions about the schemes.",
        },
      ]);
      setBotMessageAdded(true); // Mark bot message as added
    }
  }, [botMessageAdded, setMessages, messages]); // Minimal dependency array

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
    <div
      className={clsx(
        "flex flex-col",
        "bg-schemes-lightgray rounded-2xl",
        "mx-auto px-8 py-2 sm:p-[0.8rem]"
      )}
    >
      <UserQuery resetFilters={resetFilters} />
      <ChatList
        messages={messages}
        streamingMessage={currentStreamingMessage}
        scrollableDivRef={scrollableDivRef}
      />
      <Spacer y={4} />
      <ChatBar
        userInput={userInput}
        setUserInput={setUserInput}
        handleUserInput={handleUserInput}
        isBotResponseGenerating={isBotResponseGenerating}
      />
    </div>
  );
}
