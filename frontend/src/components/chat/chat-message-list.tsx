"use client";
import ReactMarkdown from "react-markdown";
import { Message } from "@/providers";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { ChatScrollAnchor } from "@/components/chat/chat-scroll-anchor";
import { MessageEntrance } from "@/components/chat/message-entrance";
import { StreamingAssistantMessage } from "@/components/chat/streaming-assistant-message";
import { StreamStatusSteps } from "@/components/chat/stream-status-steps";
import { SchemeUpdateNotice } from "@/components/chat/scheme-update-notice";
import { StatusStepsAccordion } from "@/components/chat/status-steps-accordion";
import { StatusStep } from "@/providers/chat-provider";
import FeedbackPrompt from "@/components/feedback/feedback-prompt";
import { ScrollShadow } from "@heroui/react";

const SchemesSGAvatar = () => (
  <div className="flex h-7 w-7 items-center justify-center">
    <Image
      src="/logo.svg"
      alt="Schemes.sg logo"
      width={24}
      height={24}
      className="h-6 w-6"
    />
  </div>
);

interface ChatMessageListProps {
  messages: Message[];
  streamingBlocks: string[];
  statusSteps?: StatusStep[];
  isGenerating?: boolean;
  onRate?: (index: number, rating: "up" | "down") => void;
}

export default function ChatMessageList({
  messages,
  streamingBlocks,
  statusSteps = [],
  isGenerating,
  onRate,
}: ChatMessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isUserPinnedToBottomRef = useRef(true);
  const [showJumpToLatest, setShowJumpToLatest] = useState(false);

  const isNearBottom = () => {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 96;
  };

  const handleScrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: behavior,
      });
    }
    isUserPinnedToBottomRef.current = true;
    setShowJumpToLatest(false);
  };

  const handleScroll = () => {
    const pinned = isNearBottom();
    isUserPinnedToBottomRef.current = pinned;
    setShowJumpToLatest(!pinned);
  };

  useEffect(() => {
    if (isUserPinnedToBottomRef.current) {
      handleScrollToBottom("instant");
    }
  }, [messages, streamingBlocks, statusSteps]);

  const hasStreamActivity =
    isGenerating && (streamingBlocks.some(Boolean) || statusSteps.length > 0);
  const nonEmptyStreamingBlocks = streamingBlocks.filter(
    (block) => block.trim().length > 0,
  );
  const displayedStreamingBlocks = nonEmptyStreamingBlocks.length
    ? nonEmptyStreamingBlocks
    : [""];
  const latestBotMessageIndex = messages.findLastIndex(
    (message) => message.type === "bot",
  );

  return (
    <ScrollShadow
      ref={scrollRef}
      onScroll={handleScroll}
      className="thin-scrollbar flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4 sm:px-5"
    >
      {messages.map((msg, i) => (
        <MessageEntrance
          key={i}
          className={`flex items-end gap-2.5 ${msg.type === "user" ? "flex-row-reverse" : "flex-row"}`}
        >
          {/* {msg.type === "bot" && <SchemesSGAvatar />} */}
          {/* {msg.type === "user" && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-(--schemes-blue-600) text-[10px] font-semibold text-white">
              U
            </div>
          )} */}
          {msg.type === "bot" ? (
            <div className="group/message flex w-full max-w-full flex-col items-start gap-2">
              {i === latestBotMessageIndex && msg.statusSteps?.length ? (
                <StatusStepsAccordion steps={msg.statusSteps} />
              ) : null}
              <div className="w-full break-words text-sm leading-relaxed text-(--schemes-ink-soft)">
                <div className="markdown-content prose prose-sm max-w-none text-(--schemes-ink-soft)">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              </div>
              {i === latestBotMessageIndex && msg.schemeUpdateCount ? (
                <SchemeUpdateNotice count={msg.schemeUpdateCount} />
              ) : null}
              {/* Every message in `messages` is already complete — the
                  in-flight response streams separately (StreamingAssistantMessage
                  below) and isn't in this list. So actions always show; gating
                  on isGenerating wrongly hid the previous message's actions while
                  a new query was answering. */}
              <FeedbackPrompt
                variant="rating"
                text={msg.text}
                rating={msg.rating}
                onRate={(rating) => onRate?.(i, rating)}
              />
            </div>
          ) : (
            <div className="max-w-[min(90%,450px)] wrap-break-words rounded-2xl rounded-br-md bg-(--schemes-blue-50) px-3.5 py-2.5 text-sm leading-relaxed text-(--schemes-ink)">
              {msg.text}
            </div>
          )}
        </MessageEntrance>
      ))}

      {/* Status steps, then streaming message. Full width to match a finished
          bot message — a narrower cap here would wrap the text mid-stream and
          then visibly reflow wider once the message is finalized. */}
      {hasStreamActivity && (
        <div className="flex items-end gap-2.5">
          <div className="flex w-full max-w-full flex-col items-start gap-2">
            <StreamStatusSteps steps={statusSteps} isActive={isGenerating} />
            {displayedStreamingBlocks.map((block, index) => (
              <StreamingAssistantMessage key={index} text={block} />
            ))}
          </div>
        </div>
      )}
      <ChatScrollAnchor
        show={showJumpToLatest}
        onClick={() => handleScrollToBottom()}
      />
    </ScrollShadow>
  );
}
