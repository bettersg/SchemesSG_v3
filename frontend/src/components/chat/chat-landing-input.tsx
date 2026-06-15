import { useLanguage } from "@/lib/landing-i18n";
import { motion } from "framer-motion";
import { ArrowRight, Maximize2, Minimize2, Search } from "lucide-react";
import { FormEvent, KeyboardEvent, useRef } from "react";
import { flushSync } from "react-dom";
import { duration } from "@/lib/design-system/motion";
import { useAutoGrowTextarea } from "@/hooks/use-auto-grow-textarea";

interface ChatLandingInputProps {
  query: string;
  setQuery: (q: string) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
}

function ChatLandingInput({
  query,
  setQuery,
  handleSubmit,
}: ChatLandingInputProps) {
  const { t } = useLanguage();
  const formRef = useRef<HTMLFormElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  // Caps are multiples of the 28px line-height so a clamped textarea never cuts
  // a line in half. Collapsed shows ~6 lines, expanded ~16.
  const { expanded, setExpanded, canExpand, multiline, reset } =
    useAutoGrowTextarea(textareaRef, query, {
      lineHeight: 28,
      collapsedMaxHeight: 168,
      expandedMaxHeight: 448,
    });

  const handleChipClick = (prompt: string) => {
    flushSync(() => {
      setQuery(prompt);
    });
  };

  // Enter submits; Shift+Enter inserts a newline (standard composer behaviour).
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (query.trim()) {
        reset();
        formRef.current?.requestSubmit();
      }
    }
  };

  return (
    <div className="px-4 md:px-8 flex flex-col items-center justify-center text-center z-10">
      {/* Headline */}
      <motion.h1
        className="font-serif font-bold leading-[1.08] tracking-tight text-5xl lg:text-[4.5rem] xl:text-[5rem]"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.slow, delay: 0.1 }}
      >
        {t.hero.headline.split("\n").map((line, i, arr) => (
          <span key={i}>
            {line}
            {i < arr.length - 1 && <br />}
          </span>
        ))}
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        className="mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-neutral-500"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.entrance, delay: 0.3 }}
      >
        {t.hero.subtitle}
      </motion.p>

      {/* Search bar */}
      <motion.form
        ref={formRef}
        onSubmit={handleSubmit}
        className="mt-8 w-full max-w-lg flex flex-col gap-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.entrance, delay: 0.45 }}
      >
        {/* Gemini-style composer. Single line: a pill with the icon, text and
            submit on one centered row. Multi-line: a rounded rectangle where the
            text fills the top and the icon drops to the bottom row beside the
            controls; an expand/collapse toggle is pinned top-right. */}
        <div
          className={`relative bg-white border border-neutral-300 px-4 shadow-[0_4px_24px_rgba(0,0,0,0.08)] hover:shadow-[0_6px_32px_rgba(0,0,0,0.12)] transition-shadow duration-300 focus-within:ring-2 focus-within:ring-amber-400/50 focus-within:border-amber-400 ${
            multiline
              ? "flex flex-col rounded-3xl py-3"
              : "flex items-center gap-2.5 rounded-full py-2"
          }`}
        >
          {/* Leading search icon — inline (left) on a single line. */}
          {!multiline && (
            <Search className="h-5 w-5 shrink-0 text-neutral-500 pointer-events-none" />
          )}

          {(canExpand || expanded) && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              aria-label={expanded ? t.a11y.collapseInput : t.a11y.expandInput}
              className="absolute right-3 top-3 z-10 flex size-8 items-center justify-center rounded-full text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-900"
            >
              {expanded ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>
          )}

          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder={t.chat.searchPlaceholder}
            className={`thin-scrollbar min-h-7 resize-none overscroll-contain bg-transparent text-[15px] leading-7 text-(--schemes-ink) placeholder:text-(--schemes-muted) focus:outline-none ${
              multiline ? "w-full shrink-0 pr-8" : "flex-1"
            }`}
          />

          {/* Single line: submit sits inline at the right of the pill. */}
          {!multiline && (
            <button
              type="submit"
              className="flex size-10 shrink-0 items-center justify-center rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 transition-colors duration-200 cursor-pointer shadow-sm"
              aria-label={t.a11y.search}
            >
              <ArrowRight className="h-4 w-4" />
            </button>
          )}

          {/* Multi-line: bottom controls row — icon left, submit right. */}
          {multiline && (
            <div className="mt-2 flex items-center justify-between">
              <Search className="h-5 w-5 shrink-0 text-neutral-500 pointer-events-none" />
              <button
                type="submit"
                className="flex size-10 shrink-0 items-center justify-center rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 transition-colors duration-200 cursor-pointer shadow-sm"
                aria-label={t.a11y.search}
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
        {/* <p className="mt-3 text-xs text-neutral-400">
              {t.hero.searchHint}
            </p> */}
        {/* Category chips */}
        <div className="flex flex-wrap gap-2 justify-center">
          {t.chat.categoryChips.map(({ label, prompt }) => (
            <button
              type="button"
              key={label}
              onClick={() => handleChipClick(prompt)}
              className="inline-flex items-center gap-1.5 p-3 bg-white border-2 border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
            >
              {label}
            </button>
          ))}
        </div>
      </motion.form>
    </div>
  );
}

export default ChatLandingInput;
