"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Dark code panel: a language pill and copy control in a caption bar, then the
 * sample itself.
 *
 * The dark surface is a deliberate exception to the Flat-and-light product
 * register. It stays in palette by using `--schemes-blue-900`, the deepest
 * existing navy, rather than importing another product's slate.
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

  const copy = () => {
    void navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    });
  };

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

      {/* thin-scrollbar, not no-scrollbar: samples run wider than the panel, so
          the bar has to stay discoverable — it just idles invisible until hover. */}
      <div className="thin-scrollbar overflow-x-auto px-3 pb-3">
        <pre className="min-w-full">
          <code className="block font-mono text-[12.5px] leading-[1.7] whitespace-pre text-white/70">
            {highlight(code)}
          </code>
        </pre>
      </div>
    </figure>
  );
}

/**
 * Minimal tokenizer: quoted strings only, brightened rather than coloured.
 *
 * ponytail: deliberately not a real highlighter. Monochrome by design — DESIGN.md
 * reserves colour for wayfinding ("colour carries meaning or it doesn't appear"),
 * and amber specifically for alerts, so a syntax palette has no licence here.
 * Contrast does the same job: values sit at full white against dimmed scaffolding.
 * Reach for a proper grammar only if the samples grow beyond curl and JSON.
 */
function highlight(code: string) {
  const parts = code.split(/("(?:[^"\\]|\\.)*")/g);
  return parts.map((part, index) =>
    part.startsWith('"') && part.endsWith('"') && part.length > 1 ? (
      <span key={index} className="text-white">
        {part}
      </span>
    ) : (
      <span key={index}>{part}</span>
    ),
  );
}
