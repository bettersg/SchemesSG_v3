"use client";

import type {
  Message,
  QuickReplySuggestion,
} from "@/types/chat";
import type { Scheme } from "@/types/types";
import React, {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
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
  /** True once the user has sent anything, so the navbar can guard navigation. */
  hasActiveChat: boolean;
  /** Separates an automatic post-refresh resume from a real user submit. */
  consumeIsResumedTurn: (turnKey: string) => boolean;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  /**
   * Lives here rather than in ChatPage so the navbar can open the reset modal
   * without ChatPage being its parent.
   */
  resetModalIsOpen: boolean;
  setResetModalIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
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
  const [resetModalIsOpen, setResetModalIsOpen] = useState(false);
  const [schemes, setSchemes] = useState<Scheme[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [quickReplies, setQuickReplies] = useState<QuickReplySuggestion[]>([]);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);
  const hydratedTurnKeyRef = useRef<string | null>(null);

  /**
   * True when turnKey is the turn restored from sessionStorage, meaning this
   * send is ChatPage's automatic resume rather than a user action. Clears on
   * match, so an identical question asked later still counts as a real submit.
   */
  const consumeIsResumedTurn = useCallback((turnKey: string) => {
    if (hydratedTurnKeyRef.current !== turnKey) return false;
    hydratedTurnKeyRef.current = null;
    return true;
  }, []);

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

        // A restored transcript ending on a user message gets re-fired by
        // ChatPage's mount effect. A key rather than a boolean: a boolean stays
        // true for the provider's life and would mislabel a later real submit.
        const last = stored.messages[stored.messages.length - 1];
        hydratedTurnKeyRef.current =
          last?.type === "user"
            ? `${stored.messages.length}:${last.text}`
            : null;
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
        hasActiveChat: messages.length > 0,
        consumeIsResumedTurn,
        messages,
        setMessages,
        resetModalIsOpen,
        setResetModalIsOpen,
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
