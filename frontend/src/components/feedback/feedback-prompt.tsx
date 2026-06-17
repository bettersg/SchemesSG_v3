"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Popover } from "@heroui/react";
import {
  Check,
  Copy,
  MessageSquareText,
  MoreHorizontal,
  Pencil,
  PlusCircle,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { timeout as motionTimeout } from "@/lib/design-system/motion";

type FeedbackPromptProps =
  | {
      variant: "rating";
      text: string;
      rating?: "up" | "down";
      onMsgRate: (rating: "up" | "down") => void;
      className?: string;
    }
  | {
      variant: "correction";
      schemeId: string;
      schemeName: string;
      className?: string;
    }
  | {
      variant: "contribution";
      className?: string;
    }
  | {
      variant: "general";
      className?: string;
    };

// Compact ghost icon button for the per-response action row (thumbs/copy/more).
const actionButtonBase =
  "inline-flex size-8 items-center justify-center rounded-lg text-(--schemes-muted) transition-[background-color,color] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)";

function RatingActions({
  text,
  rating,
  onRate,
  className,
}: {
  text: string;
  rating?: "up" | "down";
  onRate: (rating: "up" | "down") => void;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), motionTimeout.copiedResetMs);
    } catch {
      // Clipboard can be unavailable (insecure context / permissions); fail quietly.
    }
  };

  return (
    <div
      aria-label="Response actions"
      className={cn("flex w-fit items-center gap-0.5", className)}
    >
      <button
        type="button"
        onClick={() => onRate("up")}
        aria-label="Good response"
        aria-pressed={rating === "up"}
        title="Good response"
        className={cn(
          actionButtonBase,
          rating === "up" &&
            "bg-(--schemes-blue-50) text-(--schemes-blue-600) hover:bg-(--schemes-blue-50)",
        )}
      >
        <ThumbsUp
          size={15}
          strokeWidth={2}
          className="shrink-0"
          fill={rating === "up" ? "currentColor" : "none"}
        />
      </button>
      <button
        type="button"
        onClick={() => onRate("down")}
        aria-label="Bad response"
        aria-pressed={rating === "down"}
        title="Bad response"
        className={cn(
          actionButtonBase,
          rating === "down" &&
            "bg-(--schemes-blue-50) text-(--schemes-blue-600) hover:bg-(--schemes-blue-50)",
        )}
      >
        <ThumbsDown
          size={15}
          strokeWidth={2}
          className="shrink-0"
          fill={rating === "down" ? "currentColor" : "none"}
        />
      </button>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? "Copied" : "Copy response"}
        title={copied ? "Copied" : "Copy"}
        className={actionButtonBase}
      >
        {copied ? (
          <Check
            size={15}
            strokeWidth={2}
            className="shrink-0 text-(--schemes-blue-600)"
          />
        ) : (
          <Copy size={15} strokeWidth={2} className="shrink-0" />
        )}
      </button>
      <Popover>
        <Button
          variant="ghost"
          aria-label="More actions"
          className={cn(
            actionButtonBase,
            "min-h-0 min-w-0 border-0 bg-transparent p-0 [&_svg]:size-[15px]",
          )}
        >
          {/* Explicit h/w (not just size prop): HeroUI's Button theme otherwise
              resizes the SVG, and Firefox can collapse it to 0 without intrinsic
              dimensions, hiding the icon. */}
          <MoreHorizontal className="size-[15px] shrink-0" strokeWidth={2} />
        </Button>
        <Popover.Content
          placement="bottom start"
          className="z-50 w-44 rounded-xl border border-(--schemes-border) bg-(--schemes-surface) p-1 shadow-sm"
        >
          <Popover.Dialog className="m-0 flex flex-col p-0 outline-none">
            <Link
              href={{
                pathname: "/feedback",
                query: {
                  source: "chat",
                  ...(rating
                    ? {
                        sentiment: rating === "up" ? "positive" : "negative",
                      }
                    : {}),
                },
              }}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-(--schemes-ink-soft) no-underline transition-colors hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)"
            >
              <MessageSquareText
                size={15}
                strokeWidth={2}
                className="shrink-0"
              />
              Give feedback
            </Link>
          </Popover.Dialog>
        </Popover.Content>
      </Popover>
    </div>
  );
}

export default function FeedbackPrompt(props: FeedbackPromptProps) {
  if (props.variant === "rating") {
    return (
      <RatingActions
        text={props.text}
        rating={props.rating}
        onRate={props.onMsgRate}
        className={props.className}
      />
    );
  }

  if (props.variant === "correction") {
    return (
      <Link
        href={{
          pathname: "/feedback",
          query: {
            source: "scheme",
            schemeId: props.schemeId,
            scheme: props.schemeName,
          },
        }}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "inline-flex min-h-11 w-fit items-center gap-2 rounded-lg border border-(--schemes-blue-100) bg-white px-3 py-2 text-sm font-semibold text-(--schemes-blue-600) no-underline transition-[background-color,border-color,color] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
          props.className,
        )}
      >
        <Pencil size={16} strokeWidth={2} className="shrink-0" />
        Suggest a correction
      </Link>
    );
  }

  if (props.variant === "contribution") {
    return (
      <Link
        href="/contribute"
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "inline-flex min-h-11 w-fit items-center gap-2 rounded-lg border border-(--schemes-blue-100) bg-white px-3 py-2 text-sm font-semibold text-(--schemes-blue-600) no-underline transition-[background-color,border-color,color] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
          props.className,
        )}
      >
        <PlusCircle size={16} strokeWidth={2} className="shrink-0" />
        Contribute a new scheme
      </Link>
    );
  }

  return (
    <Link
      href="/feedback"
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex min-h-11 w-fit items-center gap-2 rounded-lg border border-(--schemes-blue-100) bg-white px-3 py-2 text-sm font-semibold text-(--schemes-blue-600) no-underline transition-[background-color,border-color,color] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)",
        props.className,
      )}
    >
      <MessageSquareText size={16} strokeWidth={2} className="shrink-0" />
      Share general feedback
    </Link>
  );
}
