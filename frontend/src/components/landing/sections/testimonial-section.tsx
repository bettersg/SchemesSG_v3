"use client";

import { motion } from "framer-motion";
import { SectionWrapper } from "@/components/landing/shared/section-wrapper";
import Image from "next/image";
import { msg } from "@lingui/core/macro";
import { useLingui } from "@lingui/react";
import {
  delay,
  motionPreset,
  transition,
  viewport,
} from "@/lib/design-system/motion";

const TESTIMONIALS = [
  {
    quote: msg({
      message:
        "I had no idea there were schemes for my situation until I tried Schemes.sg. It matched me with three programmes I actually qualified for, and one of them covered my kids' school fees. I wish I'd found this sooner.",
    }),
    author: "Sarah T.",
    role: msg({ message: "Single mother, Jurong West" }),
  },
  {
    quote: msg({
      message:
        "Schemes.sg helps our staff quickly find relevant support options for service users. We're excited to see how this tool can strengthen our work with the community.",
    }),
    author: "Care Corner Singapore",
    role: msg({ message: "Community Partner" }),
    avatar: "/landing/featured/carecorner-avatar.png",
  },
];

export function TestimonialSection() {
  const { i18n } = useLingui();

  return (
    <SectionWrapper className="bg-white">
      <div className="mx-auto max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        {TESTIMONIALS.map((item, index) => (
          <motion.div
            key={index}
            className="flex flex-col rounded-2xl border border-neutral-200/60 bg-neutral-50/50 p-8 lg:p-10"
            initial={motionPreset.fadeInUpHero.initial}
            whileInView={motionPreset.fadeInUpHero.animate}
            viewport={viewport.default}
            transition={{
              ...transition.entrance,
              delay: index * delay.testimonialStagger,
            }}
          >
            {/* Quote */}
            <blockquote className="flex-1 font-sans text-(--schemes-muted) text-lg leading-relaxed tracking-tight">
              &ldquo;{i18n._(item.quote)}&rdquo;
            </blockquote>

            {/* Author */}
            <div className="mt-6 flex items-center gap-3">
              {item.avatar ? (
                <Image
                  src={item.avatar}
                  alt={item.author}
                  width={40}
                  height={40}
                  unoptimized
                  className="h-10 w-10 shrink-0 object-contain"
                />
              ) : (
                <div className="h-10 w-10 shrink-0 rounded-full bg-gradient-to-br from-amber-300 to-amber-500 flex items-center justify-center text-neutral-900 font-bold text-sm shadow-sm">
                  {item.author.charAt(0)}
                </div>
              )}
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {item.author}
                </p>
                <p className="text-xs text-muted-foreground">
                  {i18n._(item.role)}
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </SectionWrapper>
  );
}
