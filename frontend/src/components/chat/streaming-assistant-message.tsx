"use client";

import ReactMarkdown from "react-markdown";
import { StreamStatusStep, StreamStatusSteps } from "./stream-status-steps";
import { MessageEntrance } from "./message-entrance";

type StreamingAssistantMessageProps = {
  text: string;
  statusSteps?: StreamStatusStep[];
  isStreaming?: boolean;
};

export function StreamingAssistantMessage({
  text,
  statusSteps = [],
  isStreaming = false,
}: StreamingAssistantMessageProps) {
  const hasText = text.trim().length > 0;

  return (
    <MessageEntrance className="max-w-[76%] px-3.5 py-2.5 text-sm leading-relaxed rounded-2xl rounded-bl-md bg-white border border-(--schemes-border) text-(--schemes-ink-soft) break-words">
      {hasText && (
        <div className="markdown-content prose prose-sm max-w-none text-(--schemes-ink-soft)">
          <ReactMarkdown>{text}</ReactMarkdown>
          {isStreaming && (
            <span className="ml-0.5 inline-block animate-pulse text-(--schemes-blue-600)">
              |
            </span>
          )}
        </div>
      )}
      {!hasText && (
        <StreamStatusSteps steps={statusSteps} isActive={isStreaming} />
      )}
    </MessageEntrance>
  );
}
