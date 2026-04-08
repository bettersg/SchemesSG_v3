"use client";
import ReactMarkdown from "react-markdown";
import { Message } from "@/providers";
import { RefObject } from "react";
import Image from "next/image";
import { TextShimmerWave } from "../animations/text-shimmer-wave";

const SchemesSGAvatar = () => (
  <div className="w-7 h-7 rounded-full bg-white border border-[#B5D4F4] flex items-center justify-center shrink-0">
	<Image src='logo.svg' alt="Schemes.sg logo" width={10} height={30}/>
  </div>
);

const TypingDots = () => (
  <div className="flex gap-1 items-center px-1 py-0.5">
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="w-1.5 h-1.5 rounded-full bg-[#B4B2A9] animate-bounce"
        style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.8s" }}
      />
    ))}
  </div>
);

interface ChatMessageListProps {
  messages: Message[];
  streamingMessage?: string;
  statusMessage?: string;
  isGenerating?: boolean;
  scrollableDivRef: RefObject<HTMLDivElement | null>;
}

export default function ChatMessageList({
  messages,
  streamingMessage,
  statusMessage,
  isGenerating,
  scrollableDivRef,
}: ChatMessageListProps) {
  return (
    <div
      ref={scrollableDivRef}
      className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3 thin-scrollbar"
    >
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex gap-2.5 items-end ${msg.type === "user" ? "flex-row-reverse" : "flex-row"}`}
        >
          {msg.type === "bot" && <SchemesSGAvatar />}
          {msg.type === "user" && (
            <div className="w-7 h-7 rounded-full bg-[#185FA5] flex items-center justify-center shrink-0 text-white text-[10px] font-bold">
              U
            </div>
          )}
          <div
            className={`max-w-[76%] px-3.5 py-2.5 text-sm leading-relaxed rounded-2xl break-words ${
              msg.type === "user"
                ? "bg-[#185FA5] text-white rounded-br-md"
                : "bg-white border border-[#e8eef6] text-[#444441] rounded-bl-md"
            }`}
          >
            {msg.type === "bot" ? (
              <div className="markdown-content prose prose-sm max-w-none text-[#444441]">
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            ) : (
              msg.text
            )}
          </div>
        </div>
      ))}

	  {/* Typing indicator */}
      {isGenerating && !streamingMessage && !statusMessage && (
        <div className="flex gap-2.5 items-end">
          <SchemesSGAvatar />
          <div className="px-3.5 py-2.5 rounded-2xl rounded-bl-md bg-white border border-[#e8eef6]">
            <TypingDots />
          </div>
        </div>
      )}

	  {/* Status message */}
      {isGenerating && !streamingMessage && statusMessage && (
        <div className="flex gap-2.5 items-end">
          <SchemesSGAvatar />
          <div className="px-3.5 py-2.5 rounded-2xl rounded-bl-md bg-white border border-[#e8eef6]">
			<TextShimmerWave className='font-mono text-sm' duration={1}>
            	{statusMessage}
			</TextShimmerWave>
          </div>
        </div>
      )}

      {/* Streaming */}
      {streamingMessage && (
        <div className="flex gap-2.5 items-end">
          <SchemesSGAvatar />
          <div className="max-w-[76%] px-3.5 py-2.5 text-sm leading-relaxed rounded-2xl rounded-bl-md bg-white border border-[#e8eef6] text-[#444441] break-words">
            <div className="markdown-content prose prose-sm max-w-none">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
