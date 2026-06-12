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
  // Scrollable column: the content centers via my-auto when the viewport is
  // tall enough, but scrolls from the top (with padding) on short screens
  // instead of overflowing upward under the fixed navbar.
  return (
    <div className="grain-overlay relative flex h-full w-full flex-col overflow-y-auto bg-neutral-50">
      {/* Decorative glow orbs, clipped to the viewport in their own layer so the
          600px blobs can't create horizontal scroll room on narrow screens. */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute bottom-[10%] left-[10%] h-[600px] w-[600px] rounded-full bg-amber-300/10 blur-[120px]" />
        <div className="absolute top-[10%] right-[5%] h-[600px] w-[600px] rounded-full bg-blue-300/20 blur-[120px]" />
      </div>
      <div className="my-auto flex w-full justify-center py-8">
        <ChatLandingInput
          query={draftMessage}
          setQuery={setDraftMessage}
          handleSubmit={handleSubmit}
        />
      </div>
    </div>
  );
}
