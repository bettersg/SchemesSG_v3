"use client";

import { ScrollingColumn } from "@/components/landing/shared/scrolling-column";
import { ScrollingLogoColumn } from "@/components/landing/shared/scrolling-logo-column";
import { useLanguage } from "@/lib/landing-i18n";
import { agencies } from "@/data/landing-agencies";
import ChatLanding from "@/components/chat/chat-landing";
import { useRouter } from "next/navigation";

const heroAgencies = agencies.slice(0, 12);

export function HeroSection() {
  const { t } = useLanguage();
  const router = useRouter();

  return (
    <section className="relative h-screen overflow-hidden bg-neutral-50  pt-nav">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 left-1/2 z-20 hidden w-full max-w-7xl -translate-x-1/2 lg:block"
      >
        {/* Left scrolling column */}
        <div className="absolute inset-y-20 left-0 flex w-[200px] items-center">
          <ScrollingColumn
            items={t.schemeCategories}
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
