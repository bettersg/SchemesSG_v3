"use client";
import { useChat } from "@/providers";
import { FormEvent } from "react";
import ChatLandingInput from "./chat-landing-input";

export default function ChatLanding() {
  const { draftMessage, setDraftMessage, setMessages } = useChat();

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = draftMessage.trim();
    if (!trimmed) return;
    setDraftMessage(trimmed);
    setMessages([{ type: "user", text: trimmed }]);
  };
  return (
    <div className="grain-overlay flex h-full w-screen items-center justify-center bg-neutral-50">
      <div className="pointer-events-none absolute bottom-[10%] left-[10%] h-[600px] w-[600px] rounded-full bg-amber-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute top-[10%] right-[5%] h-[600px] w-[600px] rounded-full bg-blue-300/20 blur-[120px]" />
      <ChatLandingInput
        query={draftMessage}
        setQuery={setDraftMessage}
        handleSubmit={handleSubmit}
      />
    </div>
  );
}
