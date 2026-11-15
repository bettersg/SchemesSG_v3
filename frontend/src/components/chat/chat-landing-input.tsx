import { motion } from "framer-motion";
import { ArrowRight, Maximize2, Minimize2, Search } from "lucide-react";
import { FormEvent, KeyboardEvent, useRef } from "react";
import { flushSync } from "react-dom";
import { delay, motionPreset, transition } from "@/lib/design-system/motion";
import { useAutoGrowTextarea } from "@/hooks/use-auto-grow-textarea";
import {
  productComposerExpandButton,
  productComposerLandingSurface,
  productComposerMultiline,
  productComposerSendButton,
  productComposerSingleLine,
  productComposerSurface,
  productComposerTextarea,
  productComposerTextareaMultiline,
  productComposerTextareaSingleLine,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";
import { Trans, useLingui } from "@lingui/react/macro";
import { useSchemeCount } from "@/lib/scheme-count";

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
  const { t } = useLingui();
  const schemeCount = useSchemeCount();
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
        className="font-serif font-bold leading-[1.08] tracking-tight [overflow-wrap:anywhere] text-5xl lg:text-[4.5rem] xl:text-[5rem]"
        initial={motionPreset.fadeInUpHero.initial}
        animate={motionPreset.fadeInUpHero.animate}
        transition={{ ...transition.slowEntrance, delay: delay.heroHeadline }}
      >
        <Trans comment="Landing page hero headline">
          Find the Right
          <br />
          Assistance Schemes
          <br />
          in Singapore
        </Trans>
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        className="mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-neutral-500"
        initial={motionPreset.fadeInUpMd.initial}
        animate={motionPreset.fadeInUpMd.animate}
        transition={{ ...transition.entrance, delay: delay.heroSubtitle }}
      >
        <Trans comment="Landing page hero subtitle">Describe your situation and find schemes you may qualify for. Over {schemeCount} schemes from 200+ agencies and community organisations.</Trans>
      </motion.p>

      {/* Search bar */}
      <motion.form
        ref={formRef}
        onSubmit={handleSubmit}
        className="mt-8 w-full max-w-lg flex flex-col gap-8"
        initial={motionPreset.fadeInUpMd.initial}
        animate={motionPreset.fadeInUpMd.animate}
        transition={{ ...transition.entrance, delay: delay.heroComposer }}
      >
        {/* Gemini-style composer. Single line: a pill with the icon, text and
            submit on one centered row. Multi-line: a rounded rectangle where the
            text fills the top and the icon drops to the bottom row beside the
            controls; an expand/collapse toggle is pinned top-right. */}
        <div
          className={cn(
            productComposerSurface,
            productComposerLandingSurface,
            multiline
              ? cn(productComposerMultiline, "py-3")
              : cn(productComposerSingleLine, "gap-2.5 py-2"),
          )}
        >
          {/* Leading search icon — inline (left) on a single line. */}
          {!multiline && (
            <Search className="h-5 w-5 shrink-0 text-neutral-500 pointer-events-none" />
          )}

          {(canExpand || expanded) && (
            <button
              type="button"
              onClick={() => setExpanded((v) => !v)}
              aria-label={expanded ? t`Collapse search box` : t`Expand search box`}
              className={cn(
                productComposerExpandButton,
                "right-3 top-3 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900",
              )}
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
            placeholder={t({ message: "I'm a single parent looking for financial assistance…", comment: "Placeholder text for the landing page search input" })}
            className={cn(
              productComposerTextarea,
              "min-h-7 text-[15px] leading-7 focus:outline-none",
              multiline
                ? productComposerTextareaMultiline
                : productComposerTextareaSingleLine,
            )}
          />

          {/* Single line: submit sits inline at the right of the pill. */}
          {!multiline && (
            <button
              type="submit"
              className={cn(
                productComposerSendButton,
                "size-10 cursor-pointer",
              )}
              aria-label={t({ message: "Search", comment: "Button to submit the search query" })}
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
                className={cn(
                  productComposerSendButton,
                  "size-10 cursor-pointer",
                )}
                aria-label={t({ message: "Search", comment: "Button to submit the search query" })}
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
        <div className="flex flex-wrap gap-4 justify-center">
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need financial assistance", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Financial Assistance</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need support for my family or children", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Family & Children</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need health and wellbeing support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Health & Wellbeing</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need housing or food support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Housing & Food</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need education support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Education</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need employment or training support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Employment & Training</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need support for seniors or caregivers", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Seniors & Caregiving</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need disability or transport support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Disability & Transport</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need legal or safety support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Legal & Safety</Trans>
          </button>
          <button
            type="button"
            onClick={() => handleChipClick(t({ message: "I need community support", comment: "Category chip prompt" }))}
            className="inline-flex items-center gap-1.5 py-2 px-3 bg-white border border-(--schemes-border) rounded-full text-sm font-semibold text-(--schemes-ink-soft) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) transition-colors"
          >
            <Trans comment="Category chip label">Community Support</Trans>
          </button>
        </div>
      </motion.form>
    </div>
  );
}

export default ChatLandingInput;
