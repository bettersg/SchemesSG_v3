"use client"

import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/lib/landing-i18n"

export function CTASection() {
  const { t } = useLanguage()

  return (
    <section className="relative bg-gradient-to-br from-[#042C53] to-[#185FA5] py-24 px-6 overflow-hidden text-center">
      {/* Decorative orbs — brand colours */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-[#EF9F27]/15 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-20 right-[10%] h-[300px] w-[300px] rounded-full bg-[#E6F1FB]/10 blur-[80px]" />

      <motion.div
        className="relative mx-auto max-w-2xl"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="font-[var(--font-head)] text-3xl font-bold text-white tracking-tight md:text-4xl lg:text-5xl">
          {t.cta.headline}
        </h2>
        <p className="mt-5 text-white/70 text-lg leading-relaxed max-w-xl mx-auto">
          {t.cta.subtitle}
        </p>
        <div className="mt-9 flex flex-wrap gap-3 justify-center">
          <Button
            size="lg"
            className="rounded-full bg-[#EF9F27] text-white hover:bg-[#BA7517] px-10 py-6 text-base font-bold gap-2 shadow-none cursor-pointer transition-all duration-200 border-0"
            asChild
          >
            <a href="/">
              {t.cta.button}
              <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
          <Button
            size="lg"
            className="rounded-full bg-white/10 text-white hover:bg-white/20 border border-white/20 px-8 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200"
            asChild
          >
            <a href="/explore">
              Browse all schemes
            </a>
          </Button>
        </div>
        <p className="mt-5 text-sm text-white/50">{t.cta.note}</p>
      </motion.div>
    </section>
  )
}
