"use client";

import { useState } from "react";
import { ScrollingColumn } from "@/components/landing/shared/scrolling-column";
import { ScrollingLogoColumn } from "@/components/landing/shared/scrolling-logo-column";
import { useLanguage } from "@/lib/landing-i18n";
import { agencies } from "@/data/landing-agencies";
import ChatLandingInput from "@/components/chat/chat-landing-input";
import { useChat } from "@/providers";
import { useRouter } from "next/navigation";

const heroAgencies = agencies.slice(0, 12);

export function HeroSection() {
  const { t } = useLanguage();
  const [query, setQuery] = useState("");
  const { setMessages } = useChat();
  const router = useRouter();

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setMessages([{ type: "user", text: query }]);
    router.push("/");
  }

  return (
    <section className="relative min-h-0 lg:min-h-[100svh] flex items-center overflow-hidden bg-neutral-50 grain-overlay">
      {/* Gradient glow orbs */}
      <div className="pointer-events-none absolute bottom-[10%] left-[10%] h-[600px] w-[600px] rounded-full bg-amber-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute top-[10%] right-[5%] h-[600px] w-[600px] rounded-full bg-blue-300/20 blur-[120px]" />

      <div className="relative mx-auto w-full max-w-7xl grid grid-cols-1 lg:grid-cols-[200px_1fr_200px] gap-8 px-6 pt-28 pb-16 lg:py-20">
        {/* Left scrolling column — scheme categories */}
        <div className="hidden lg:flex items-center">
          <ScrollingColumn
            items={t.schemeCategories}
            direction="up"
            highlightIndex={3}
            speed={28}
          />
        </div>

        {/* Center content */}
        <ChatLandingInput
          query={query}
          setQuery={setQuery}
          handleSubmit={handleSubmit}
        />

        {/* Right scrolling column — agency logos */}
        <div className="hidden lg:flex items-center justify-end">
          <ScrollingLogoColumn agencies={heroAgencies} speed={32} />
        </div>
      </div>
    </section>
  );
}
