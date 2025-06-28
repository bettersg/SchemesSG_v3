"use client";

import { SearchResScheme } from "@/components/schemes/schemes-list";
import { HeroUIProvider } from "@heroui/react";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { analytics } from "./firebaseConfig"; // Adjust path as needed


// Chat Context
export type Message = {
  type: "user" | "bot";
  text: string;
};

type ChatContextType = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  sessionId: string;
  setSessionId: React.Dispatch<React.SetStateAction<string>>;
  schemes: SearchResScheme[];
  setSchemes: React.Dispatch<React.SetStateAction<SearchResScheme[]>>;
  userQuery: string;
  setUserQuery: (query: string) => void;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [schemes, setSchemes] = useState<SearchResScheme[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);
  const [userQuery, setUserQuery] = useState("");

  // Load data from localStorage on mount
  useEffect(() => {
    if (!isInitialized) {
      try {
        const storedSchemes = localStorage.getItem("schemes");
        const storedMessages = localStorage.getItem("userMessages");
        const storedSessionId = localStorage.getItem("sessionID");
        const storedUserQuery = localStorage.getItem("userQuery");

        if (storedSchemes) {
          const parsedSchemes = JSON.parse(storedSchemes);
          setSchemes(parsedSchemes);
        }
        if (storedMessages) {
          const parsedMessages = JSON.parse(storedMessages);
          setMessages(parsedMessages);
        }
        if (storedSessionId) {
          setSessionId(storedSessionId);
        }
        if (storedUserQuery) {
          setUserQuery(storedUserQuery);
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

  useEffect(() => {
    if (isInitialized && sessionId) {
      try {
        localStorage.setItem("sessionID", sessionId);
      } catch (error) {
        console.error("Error saving sessionId to localStorage:", error);
      }
    }
  }, [sessionId, isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        if (userQuery) {
          localStorage.setItem("userQuery", userQuery);
        } else {
          localStorage.removeItem("userQuery");
        }
      } catch (error) {
        console.error("Error saving userQuery to localStorage:", error);
      }
    }
  }, [userQuery, isInitialized]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        schemes,
        setSchemes,
        sessionId,
        setSessionId,
        userQuery,
        setUserQuery,
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
  // Firebase Analytics
  useEffect(() => {
    if (analytics) {
      console.log("Firebase Analytics initialized.");
    }
  }, []);

  return (
    <HeroUIProvider>
      <ChatProvider>{children}</ChatProvider>
    </HeroUIProvider>
  );
}
