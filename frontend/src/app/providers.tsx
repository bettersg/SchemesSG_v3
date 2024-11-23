'use client';

import { NextUIProvider } from '@nextui-org/react';
import React, { createContext, useContext, useState, ReactNode } from 'react';

// Chat Context
export type Message = {
  type: 'user' | 'bot';
  text: string;
};

type ChatContextType = {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
};

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<Message[]>([]);

  return (
    <ChatContext.Provider value={{ messages, setMessages }}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
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
