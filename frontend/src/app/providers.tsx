"use client";

import { Scheme } from "@/components/schemes/schemes-list";
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
  userQuery: string;
  setUserQuery: React.Dispatch<React.SetStateAction<string>>;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  schemes: Scheme[];
  setSchemes: React.Dispatch<React.SetStateAction<Scheme[]>>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userQuery, setUserQuery] = useState<string>("");
  const [schemes, setSchemes] = useState<Scheme[]>([]);

  useEffect(() => {
    const savedSchemes = localStorage.getItem("schemes");
    if (savedSchemes) {
      setSchemes(JSON.parse(savedSchemes));
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("schemes", JSON.stringify(schemes));
  }, [schemes]);

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        userQuery,
        setUserQuery,
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
