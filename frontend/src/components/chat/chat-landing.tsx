"use client";
import { useChat } from "@/providers";
import { useRef, useState } from "react";
import { Spinner } from "@heroui/react";
import ChatLandingInput from "./chat-landing-input";

const CATEGORY_CHIPS = [
  { label: "Financial Aid", emoji: "💰" },
  { label: "Healthcare", emoji: "🏥" },
  { label: "Mental Health", emoji: "🧠" },
  { label: "Family Support", emoji: "👨‍👩‍👧" },
  { label: "Housing", emoji: "🏠" },
  { label: "Employment", emoji: "💼" },
  { label: "Food Assistance", emoji: "🍚" },
  { label: "Education", emoji: "📚" },
];

export default function ChatLanding() {
  const { setMessages } = useChat();
  const [query, setQuery] = useState("");

  const handleSubmit = (e: SubmitEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setMessages([{ type: "user", text: query }]);
  };
  return (
    <div className="w-screen h-full flex justify-center items-center">
		<ChatLandingInput
		  query={query}
		  setQuery={setQuery}
		  handleSubmit={handleSubmit}
		/>
	</div>
  );
}
