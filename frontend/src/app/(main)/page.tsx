"use client";
import { useChat } from "@/providers";
import ChatPage from "@/components/chat/chat-page";
import ChatLanding from "@/components/chat/chat-landing";

export default function Home() {
  const { messages } = useChat();

  if (messages.length > 0) {
    return (
      <ChatPage/>
    );
  }

  return <ChatLanding />;
}