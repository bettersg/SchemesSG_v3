"use client";

import ReactMarkdown from "react-markdown";
import { MessageEntrance } from "./message-entrance";

type StreamingAssistantMessageProps = {
  text: string;
};

export function StreamingAssistantMessage({
  text,
}: StreamingAssistantMessageProps) {
  if (!text.trim()) return null;

  return (
    <MessageEntrance
      aria-live="polite"
      className="w-full max-w-full break-words text-sm leading-relaxed text-(--schemes-ink-soft)"
    >
      <div className="markdown-content prose prose-sm max-w-none text-(--schemes-ink-soft)">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
    </MessageEntrance>
  );
}
