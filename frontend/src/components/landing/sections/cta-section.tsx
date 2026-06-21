"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/landing/ui/button";
import { useLanguage } from "@/lib/landing-i18n";
import Link from "next/link";
import {
  cssTransition,
  motionPreset,
  transition,
  viewport,
} from "@/lib/design-system/motion";

export function CTASection() {
  const { t } = useLanguage();

  return (
    <section className="relative bg-neutral-950 py-24 px-6 overflow-hidden">
      {/* Decorative gradient orbs */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-amber-400/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-20 right-[10%] h-[300px] w-[300px] rounded-full bg-blue-400/5 blur-[80px]" />

      <motion.div
        className="relative mx-auto max-w-2xl text-center"
        initial={motionPreset.fadeInUpHero.initial}
        whileInView={motionPreset.fadeInUpHero.animate}
        viewport={viewport.default}
        transition={transition.entrance}
      >
        <h2 className="font-serif text-3xl font-bold text-white tracking-tight md:text-4xl lg:text-5xl">
          {t.cta.headline}
        </h2>
        <p className="mt-5 text-neutral-400 text-lg leading-relaxed max-w-xl mx-auto">
          {t.cta.subtitle}
        </p>
        <Link href="/">
          <Button
            size="lg"
            className={`${cssTransition.allState} mt-9 rounded-full bg-amber-400 text-neutral-900 hover:bg-amber-500 px-10 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer border-0`}
          >
            {t.cta.button}
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
        <p className="mt-4 text-sm text-neutral-500">{t.cta.note}</p>
      </motion.div>
    </section>
  );
}
