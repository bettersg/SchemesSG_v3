"use client";
import { useChat } from "@/providers";
import { FormEvent } from "react";
import ChatLandingInput from "./chat-landing-input";
import { cn } from "@/lib/utils";

type ChatLandingProps = {
  onSubmitSuccess?: () => void;
};

export default function ChatLanding({ onSubmitSuccess }: ChatLandingProps) {
  const { draftMessage, setDraftMessage, setMessages } = useChat();

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const trimmed = draftMessage.trim();
    if (!trimmed) return;
    setDraftMessage(trimmed);
    setMessages([{ type: "user", text: trimmed }]);
    onSubmitSuccess?.();
  };
  // Scrollable column: the content centers via my-auto when the viewport is
  // tall enough, but scrolls from the top (with padding) on short screens
  // instead of overflowing upward under the fixed navbar.
  return (
    <div
      className={cn(
        "grain-overlay h-full w-full overflow-y-auto bg-neutral-50",
      )}
    >
      <div className="relative flex min-h-full w-full flex-col overflow-x-clip">
        {/* Decorative glow orbs attach to this in-flow wrapper, so the layer
            grows with the scrollable landing content instead of stopping at the
            initial scrollport height on compact mobile screens. */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
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
    </div>
  );
}
