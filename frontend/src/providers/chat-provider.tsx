"use client";

import { Scheme } from "@/types/types";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

export type UserMessage = {
  type: "user";
  text: string;
};

export type StatusStep = {
  id: string;
  label: string;
  message: string;
  phase?: string;
};

export type BotMessage = {
  type: "bot";
  text: string;
  schemeUpdateCount?: number;
  statusSteps?: StatusStep[];
};

export type Message = UserMessage | BotMessage;

export type QuickReplySuggestion = {
  label: string;
  value: string;
};

type ChatContextType = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  sessionId: string;
  setSessionId: React.Dispatch<React.SetStateAction<string>>;
  schemes: Scheme[];
  setSchemes: React.Dispatch<React.SetStateAction<Scheme[]>>;
  quickReplies: QuickReplySuggestion[];
  setQuickReplies: React.Dispatch<React.SetStateAction<QuickReplySuggestion[]>>;
  showQuickReplies: boolean;
  setShowQuickReplies: React.Dispatch<React.SetStateAction<boolean>>;
  draftMessage: string;
  setDraftMessage: React.Dispatch<React.SetStateAction<string>>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);
const QUICK_REPLIES_STORAGE_KEY = "quickReplies";

function parseQuickReplies(value: string | null): QuickReplySuggestion[] {
  if (!value) return [];

  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) return [];

    return parsed.filter(
      (reply): reply is QuickReplySuggestion =>
        reply &&
        typeof reply.label === "string" &&
        typeof reply.value === "string",
    );
  } catch (error) {
    console.error("Error loading quick replies from sessionStorage:", error);
    return [];
  }
}

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [quickReplies, setQuickReplies] = useState<QuickReplySuggestion[]>([]);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (!isInitialized) {
      try {
        const storedSchemes = sessionStorage.getItem("schemes");
        const storedMessages = sessionStorage.getItem("userMessages");
        const storedSessionId = sessionStorage.getItem("sessionID");
        const storedQuickReplies = parseQuickReplies(
          sessionStorage.getItem(QUICK_REPLIES_STORAGE_KEY),
        );

        if (storedSchemes) {
          const parsedSchemes = JSON.parse(storedSchemes);
          setSchemes(parsedSchemes);
        }
        if (storedMessages) {
          const parsedMessages = JSON.parse(storedMessages);
          setMessages(parsedMessages);
        }
        if (storedSessionId && storedSessionId.trim() !== "") {
          const parsedSessionId = JSON.parse(storedSessionId);
          if (
            parsedSessionId &&
            typeof parsedSessionId === "string" &&
            parsedSessionId.length > 10
          ) {
            setSessionId(parsedSessionId);
          }
        }
        if (storedQuickReplies.length > 0) {
          setQuickReplies(storedQuickReplies);
          setShowQuickReplies(true);
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
    if (!isInitialized) return;

    try {
      if (quickReplies.length > 0) {
        sessionStorage.setItem(
          QUICK_REPLIES_STORAGE_KEY,
          JSON.stringify(quickReplies),
        );
      } else {
        sessionStorage.removeItem(QUICK_REPLIES_STORAGE_KEY);
      }
    } catch (error) {
      console.error("Error saving quick replies to sessionStorage:", error);
    }
  }, [quickReplies, isInitialized]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        schemes,
        setSchemes,
        sessionId,
        setSessionId,
        quickReplies,
        setQuickReplies,
        showQuickReplies,
        setShowQuickReplies,
        draftMessage,
        setDraftMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
