"use client";

import { ScrollingColumn } from "@/components/landing/shared/scrolling-column";
import { ScrollingLogoColumn } from "@/components/landing/shared/scrolling-logo-column";
import { agencies } from "@/data/landing-agencies";
import ChatLanding from "@/components/chat/chat-landing";
import { useRouter } from "next/navigation";
import { msg } from "@lingui/core/macro";
import { useLingui } from "@lingui/react";

const heroAgencies = agencies.slice(0, 12);

const SCHEME_CATEGORIES = [
  msg({
    message: "Health & Wellbeing",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Education",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Housing & Food",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Financial Assistance",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Seniors & Caregiving",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Disability & Transport",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Employment & Training",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Family & Children",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Legal & Safety",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
  msg({
    message: "Community Support",
    comment:
      "Scheme type shown in the scrolling list beside the home page search",
  }),
];

export function HeroSection() {
  const router = useRouter();
  const { i18n } = useLingui();

  return (
    <section className="relative h-screen overflow-hidden bg-neutral-50  pt-nav">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 left-1/2 z-20 hidden w-full max-w-7xl -translate-x-1/2 lg:block"
      >
        {/* Left scrolling column */}
        <div className="absolute inset-y-20 left-0 flex w-[200px] items-center">
          <ScrollingColumn
            items={SCHEME_CATEGORIES.map((category) => i18n._(category))}
            direction="up"
            highlightIndex={3}
            speed={28}
          />
        </div>
        {/* Right scrolling logo column */}
        <div className="absolute inset-y-20 right-0 flex w-[200px] items-center justify-end">
          <ScrollingLogoColumn agencies={heroAgencies} speed={32} />
        </div>
      </div>
      {/* Center main landing page */}
      <ChatLanding onSubmitSuccess={() => router.push("/")} />
    </section>
  );
}
