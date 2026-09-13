"use client";

import type {
  Message,
  QuickReplySuggestion,
} from "@/types/chat";
import type { Scheme } from "@/types/types";
import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  CHAT_STORAGE_KEYS,
  deserializeChatState,
  serializeChatState,
} from "@/lib/chat-storage";

export type {
  BotMessage,
  Message,
  QuickReplySuggestion,
  StatusStep,
  UserMessage,
} from "@/types/chat";

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
        const stored = deserializeChatState({
          schemes: sessionStorage.getItem(CHAT_STORAGE_KEYS.schemes),
          messages: sessionStorage.getItem(CHAT_STORAGE_KEYS.messages),
          sessionId: sessionStorage.getItem(CHAT_STORAGE_KEYS.sessionId),
          quickReplies: sessionStorage.getItem(
            CHAT_STORAGE_KEYS.quickReplies,
          ),
        });

        setSchemes(stored.schemes);
        setMessages(stored.messages);
        setSessionId(stored.sessionId);
        setQuickReplies(stored.quickReplies);
        if (stored.quickReplies.length > 0) {
          setShowQuickReplies(true);
        }
      } catch (error) {
        console.error("Error loading from sessionStorage:", error);
      } finally {
        setIsInitialized(true);
      }
    }
  }, [isInitialized]);

  useEffect(() => {
    if (!isInitialized) return;

    try {
      const stored = serializeChatState({
        schemes,
        messages,
        sessionId,
        quickReplies,
      });

      const entries = [
        [CHAT_STORAGE_KEYS.schemes, stored.schemes],
        [CHAT_STORAGE_KEYS.messages, stored.messages],
        [CHAT_STORAGE_KEYS.sessionId, stored.sessionId],
        [CHAT_STORAGE_KEYS.quickReplies, stored.quickReplies],
      ] as const;
      entries.forEach(([key, value]) => {
        try {
          if (value === null) sessionStorage.removeItem(key);
          else sessionStorage.setItem(key, value);
        } catch (error) {
          console.error(`Error saving ${key} to sessionStorage:`, error);
        }
      });
    } catch (error) {
      console.error("Error saving to sessionStorage:", error);
    }
  }, [isInitialized, messages, quickReplies, schemes, sessionId]);

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
