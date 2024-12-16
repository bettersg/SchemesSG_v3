"use client";

import { SearchResScheme } from "@/components/schemes/schemes-list";
import { NextUIProvider } from "@nextui-org/react";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

// Chat Context
export type Message = {
  type: "user" | "bot";
  text: string;
};

type ChatContextType = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  schemes: SearchResScheme[];
  setSchemes: React.Dispatch<React.SetStateAction<SearchResScheme[]>>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [schemes, setSchemes] = useState<SearchResScheme[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // Load data from localStorage on mount
  useEffect(() => {
    if (!isInitialized) {
      try {
        const storedSchemes = localStorage.getItem("schemes");
        const storedMessages = localStorage.getItem("userMessages");

        if (storedSchemes) {
          const parsedSchemes = JSON.parse(storedSchemes);
          setSchemes(parsedSchemes);
        }
        if (storedMessages) {
          const parsedMessages = JSON.parse(storedMessages);
          setMessages(parsedMessages);
        }

        setIsInitialized(true);
      } catch (error) {
        console.error("Error loading from localStorage:", error);
      }
    }
  }, [isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        localStorage.setItem("schemes", JSON.stringify(schemes));
      } catch (error) {
        console.error("Error saving schemes to localStorage:", error);
      }
    }
  }, [schemes, isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        localStorage.setItem("userMessages", JSON.stringify(messages));
      } catch (error) {
        console.error("Error saving messages to localStorage:", error);
      }
    }
  }, [messages, isInitialized]);
  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        schemes,
        setSchemes,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

// Combined Providers
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextUIProvider>
      <ChatProvider>{children}</ChatProvider>
    </NextUIProvider>
  );
}
