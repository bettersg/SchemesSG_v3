"use client";

import { useState } from "react";
import { useChat } from "@/providers";
import ChatPage from "@/components/chat/chat-page";
import ChatLanding from "@/components/chat/chat-landing";

export default function ChatHome() {
  const { messages } = useChat();

  // Latches as soon as this visit has any message — landing submit, hero → "/"
  // nav and sessionStorage rehydration all funnel through `messages` — so a
  // first send that fails and gets spliced back out (rollbackActiveRequest in
  // chat-page.tsx) can't swap the landing screen back in and unmount the chat
  // view's error banner with it. Deliberately mount-scoped: navigating away
  // discards that banner anyway, so a later visit with an empty chat starts on
  // the landing screen rather than a blank chat view.
  const [hasStartedChat, setHasStartedChat] = useState(false);
  if (messages.length > 0 && !hasStartedChat) setHasStartedChat(true);

  if (hasStartedChat) {
    return <ChatPage onReset={() => setHasStartedChat(false)} />;
  }

  return <ChatLanding />;
}
