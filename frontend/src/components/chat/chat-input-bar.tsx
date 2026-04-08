"use client";
import { useState, useRef, KeyboardEvent } from "react";
import { Spinner } from "@heroui/react";

interface ChatInputBarProps {
  onSend: (message: string) => void;
  isGenerating: boolean;
}

export default function ChatInputBar({ onSend, isGenerating }: ChatInputBarProps) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isGenerating) return;
    onSend(trimmed);
    setValue("");
    if (ref.current) {
      ref.current.style.height = "auto";
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    if (ref.current) {
      ref.current.style.height = "auto";
      ref.current.style.height = Math.min(ref.current.scrollHeight, 120) + "px";
    }
  };

  return (
    <div className="bg-white border-t border-[#e8eef6] px-3 py-2.5 shrink-0">
      <div className="flex gap-2.5 items-end bg-[#f7f9fc] border-[1.5px] border-[#e0eaf5] rounded-xl px-3.5 py-2 focus-within:border-[#378ADD] focus-within:bg-white transition-all">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKey}
          onInput={handleInput}
          placeholder="Ask a follow-up question…"
          rows={1}
          className="flex-1 resize-none bg-transparent outline-none text-sm text-[#444441] placeholder:text-[#B4B2A9] leading-relaxed min-h-[24px] max-h-[120px]"
        />
        <button
          onClick={handleSend}
          disabled={isGenerating || !value.trim()}
          className="w-8 h-8 rounded-lg bg-[#185FA5] flex items-center justify-center shrink-0 transition-all hover:bg-[#0C447C] disabled:opacity-40 disabled:cursor-not-allowed mb-0.5"
        >
          {isGenerating ? (
            <Spinner size="sm" color="white" />
          ) : (
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M14 8L2 2l2 6-2 6 12-6z" fill="white"/>
            </svg>
          )}
        </button>
      </div>
      <p className="text-center text-[10px] text-[#B4B2A9] mt-1.5 flex items-center justify-center gap-1">
        <svg width="9" height="9" viewBox="0 0 11 11" fill="none">
          <path d="M5.5 1L9 3V6C9 7.66 7.44 9.08 5.5 10C3.56 9.08 2 7.66 2 6V3L5.5 1Z" stroke="#B4B2A9" strokeWidth="1.2"/>
        </svg>
        Anonymous · No personal data stored
      </p>
    </div>
  );
}
