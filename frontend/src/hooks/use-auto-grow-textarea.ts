"use client";
import { RefObject, useCallback, useLayoutEffect, useState } from "react";

interface UseAutoGrowTextareaOptions {
  /** Height of a single line (px) — content taller than this is "multiline". */
  lineHeight: number;
  /** Cap while collapsed; past this the textarea scrolls internally. */
  collapsedMaxHeight: number;
  /** Cap while expanded — a tall composer the user opts into. */
  expandedMaxHeight: number;
}

/**
 * Gemini-style composer sizing: a textarea that grows with its content up to a
 * fixed collapsed height (then scrolls), with an opt-in expanded mode that
 * grows to a much taller cap.
 *
 * - `multiline` flips once content wraps past one line, so the composer can
 *   switch from a single-row pill to a stacked rounded-rectangle.
 * - `canExpand` gates the expand/collapse toggle to when content actually
 *   overflows the collapsed height.
 */
export function useAutoGrowTextarea(
  ref: RefObject<HTMLTextAreaElement | null>,
  value: string,
  {
    lineHeight,
    collapsedMaxHeight,
    expandedMaxHeight,
  }: UseAutoGrowTextareaOptions,
) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const [multiline, setMultiline] = useState(false);

  const resize = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    const cap = expanded ? expandedMaxHeight : collapsedMaxHeight;
    // Measure the true height of the actual VALUE. Two things would otherwise
    // inflate scrollHeight and wrongly flag the composer as multi-line:
    //   - a CSS min-height (reads as an extra line on some high-DPR mobile);
    //   - a long placeholder that wraps to 2 lines on a narrow textarea.
    // Neutralise both, collapse to 0, measure, then restore.
    const prevMinHeight = el.style.minHeight;
    const placeholder = el.placeholder;
    el.placeholder = "";
    el.style.minHeight = "0px";
    el.style.height = "0px";
    const natural = el.scrollHeight;
    el.style.height = Math.min(natural, cap) + "px";
    el.style.minHeight = prevMinHeight;
    el.placeholder = placeholder;
    setMultiline(natural > lineHeight + 1);
    // The expand affordance is only meaningful once content exceeds the
    // collapsed cap (i.e. there's more to reveal than the collapsed view shows).
    const overflows = natural > collapsedMaxHeight + 1;
    setCanExpand(overflows);
    // Once content shrinks below the collapsed cap there's nothing left to
    // expand, so drop expanded state — otherwise its toggle lingers and
    // overlaps the inline submit button on the single-line pill.
    if (!overflows) setExpanded(false);
  }, [ref, expanded, lineHeight, collapsedMaxHeight, expandedMaxHeight]);

  useLayoutEffect(() => {
    resize();
  }, [value, resize]);

  // Collapsing back: drop expanded state and re-clamp on the next frame.
  const reset = useCallback(() => {
    setExpanded(false);
    const el = ref.current;
    if (el) el.style.height = "auto";
  }, [ref]);

  return { expanded, setExpanded, canExpand, multiline, reset };
}
