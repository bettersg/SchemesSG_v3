"use client";

import { useChat } from "@/providers";
import ChatPage from "@/components/chat/chat-page";
import ChatLanding from "@/components/chat/chat-landing";

export default function ChatHome() {
  const { messages, hasStartedChat } = useChat();

  // `hasStartedChat` covers the case where the first message's send failed
  // and rollbackActiveRequest (chat-page.tsx) spliced it back out, leaving
  // `messages` empty again — without it, ChatHome would swap back to the
  // landing screen and silently drop the in-flight error state with it.
  if (messages.length > 0 || hasStartedChat) {
    return <ChatPage />;
  }

  return <ChatLanding />;
}
