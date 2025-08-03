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

// parse item stored in local storage as value
// function retrieveLocalStorage(key: string) {
//   const item = localStorage.getItem(key);
//   if (item) {
//     try {
//       const { value, expiration } = JSON.parse(item);
//       if (value && Date.now() < expiration) {
//         return value;
//       }
//     } catch (error) {
//       console.error("Error loading from localStorage:", error);
//     }
//   }
//   return null;
// }

// function storeLocalStorage(key: string, value: unknown) {
//   localStorage.setItem(
//     key,
//     JSON.stringify({
//       value: value,
//       expiration: Date.now() + 12 * 60 * 60 * 1000,
//     })
//   );
// }

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [schemes, setSchemes] = useState<SearchResScheme[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);
  const [userQuery, setUserQuery] = useState("");

  // Load data from sessionStorage on mount
  useEffect(() => {
    if (!isInitialized) {
      try {
        const storedSchemes = sessionStorage.getItem("schemes");
        const storedMessages = sessionStorage.getItem("userMessages");
        const storedSessionId = sessionStorage.getItem("sessionID");
        const storedUserQuery = sessionStorage.getItem("userQuery");

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
        console.error("Error loading from sessionStorage:", error);
      }
    }
  }, [isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        sessionStorage.setItem("schemes", JSON.stringify(schemes));
      } catch (error) {
        console.error("Error saving schemes to sessionStorage:", error);
      }
    }
  }, [schemes, isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        sessionStorage.setItem("userMessages", JSON.stringify(messages));
      } catch (error) {
        console.error("Error saving messages to sessionStorage:", error);
      }
    }
  }, [messages, isInitialized]);

  useEffect(() => {
    if (isInitialized && sessionId) {
      try {
        sessionStorage.setItem("sessionID", JSON.stringify(sessionId));
      } catch (error) {
        console.error("Error saving sessionId to sessionStorage:", error);
      }
    }
  }, [sessionId, isInitialized]);

  useEffect(() => {
    if (isInitialized) {
      try {
        if (userQuery) {
          sessionStorage.setItem("userQuery", JSON.stringify(userQuery));
        } else {
          sessionStorage.removeItem("userQuery");
        }
      } catch (error) {
        console.error("Error saving userQuery to sessionStorage:", error);
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
