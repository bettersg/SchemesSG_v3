"use client";

import { Check, Copy } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Dark code panel, in the Stripe API reference arrangement: a language pill and
 * copy control in a caption bar, gutter line numbers, and the sample itself.
 *
 * The dark surface is a deliberate exception to the Flat-and-light product
 * register: this docs surface follows a pinned reference. It stays in palette by
 * using `--schemes-blue-900`, the deepest existing navy, rather than importing
 * another product's slate.
 */
export function CodeBlock({
  code,
  language,
  caption,
  copyLabel,
  copiedLabel,
  className,
}: {
  code: string;
  language: string;
  caption?: string;
  copyLabel: string;
  copiedLabel: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  const lines = useMemo(() => code.split("\n"), [code]);

  const copy = useCallback(() => {
    void navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    });
  }, [code]);

  return (
    <figure
      className={cn(
        "overflow-hidden rounded-[0.625rem] bg-(--schemes-blue-900)",
        className,
      )}
    >
      <figcaption className="flex items-center justify-between gap-3 px-3 py-2">
        <span className="truncate text-[10px] font-semibold tracking-widest text-(--schemes-blue-100) uppercase">
          {caption}
        </span>
        <div className="flex shrink-0 items-center gap-1">
          <span className="rounded-md bg-white/10 px-2 py-1 font-mono text-[11px] font-semibold text-white">
            {language}
          </span>
          <button
            type="button"
            onClick={copy}
            aria-label={copied ? copiedLabel : copyLabel}
            title={copied ? copiedLabel : copyLabel}
            className="inline-flex h-11 w-11 items-center justify-center rounded-md text-(--schemes-blue-100) transition-colors duration-150 ease-out hover:bg-white/10 hover:text-white focus-visible:ring-2 focus-visible:ring-(--schemes-blue-400) focus-visible:outline-none"
          >
            {copied ? (
              <Check aria-hidden className="h-4 w-4" />
            ) : (
              <Copy aria-hidden className="h-4 w-4" />
            )}
          </button>
        </div>
      </figcaption>

      <div className="overflow-x-auto pb-3">
        <pre className="min-w-full">
          <code className="block font-mono text-[12.5px] leading-[1.7]">
            {lines.map((line, index) => (
              <span key={index} className="flex">
                <span
                  aria-hidden
                  className="sticky left-0 w-10 shrink-0 bg-(--schemes-blue-900) pr-3 text-right text-(--schemes-blue-100)/50 select-none"
                >
                  {index + 1}
                </span>
                <span className="pr-4 whitespace-pre text-white">
                  {highlight(line)}
                </span>
              </span>
            ))}
          </code>
        </pre>
      </div>
    </figure>
  );
}

/**
 * Minimal tokenizer: quoted strings and shell comments only.
 *
 * ponytail: deliberately not a real highlighter. All-white JSON on a dark panel
 * reads flat, and these two rules recover most of the structure. Reach for a
 * proper grammar only if the samples grow beyond curl and JSON.
 */
function highlight(line: string) {
  const trimmed = line.trimStart();
  if (trimmed.startsWith("#")) {
    return <span className="text-(--schemes-blue-100)/70">{line}</span>;
  }

  const parts = line.split(/("(?:[^"\\]|\\.)*")/g);
  return parts.map((part, index) =>
    part.startsWith('"') && part.endsWith('"') && part.length > 1 ? (
      <span key={index} className="text-(--schemes-amber-100)">
        {part}
      </span>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}
