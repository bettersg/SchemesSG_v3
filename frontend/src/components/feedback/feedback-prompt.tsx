"use client";

import Link from "next/link";
import {
  MessageSquareText,
  Pencil,
  PlusCircle,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

type FeedbackPromptProps =
  | {
      variant: "rating";
      className?: string;
    }
  | {
      variant: "correction";
      schemeId: string;
      schemeName: string;
      section?: string;
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

const iconLinkClass =
  "inline-flex size-11 items-center justify-center rounded-lg text-(--schemes-muted) transition-[background-color,color,opacity] hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600) focus-visible:bg-(--schemes-blue-50) focus-visible:text-(--schemes-blue-600) focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)";

export default function FeedbackPrompt(props: FeedbackPromptProps) {
  if (props.variant === "rating") {
    return (
      <div
        aria-label="Rate this response"
        className={cn(
          "flex w-fit items-center gap-0.5 text-xs text-(--schemes-muted)",
          props.className,
        )}
      >
        <span className="mr-1">Was this helpful?</span>
        <Link
          href={{
            pathname: "/feedback",
            query: { source: "chat", sentiment: "positive" },
          }}
          aria-label="This response was helpful"
          title="This response was helpful"
          className={iconLinkClass}
          target="_blank"
          rel="noopener noreferrer"
        >
          <ThumbsUp size={16} strokeWidth={2} className="shrink-0" />
        </Link>
        <Link
          href={{
            pathname: "/feedback",
            query: { source: "chat", sentiment: "negative" },
          }}
          aria-label="This response was not helpful"
          title="This response was not helpful"
          className={iconLinkClass}
          target="_blank"
          rel="noopener noreferrer"
        >
          <ThumbsDown size={16} strokeWidth={2} className="shrink-0" />
        </Link>
      </div>
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
            ...(props.section ? { section: props.section } : {}),
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
