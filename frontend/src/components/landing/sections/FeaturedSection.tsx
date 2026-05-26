"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/lib/landing-i18n"
import { cn } from "@/lib/utils"

const featuredLogos = [
  { name: "Channel NewsAsia", src: "/landing/featured/cna-logo.svg" },
  { name: "Lianhe Zaobao", src: "/landing/featured/lianhe-zaobao-logo.svg" },
  { name: "Money FM", src: "/landing/featured/moneyfm-logo.svg" },
  { name: "Better.sg", src: "/landing/featured/bettersg-logo.svg" },
  { name: "Sengkang Town Council", src: "/landing/featured/sengkang-logo.svg" },
  { name: "Hatch", src: "/landing/featured/hatch-logo.png" },
]

const partnerLogos = [
  { name: "Singapore Association of Social Workers", src: "/landing/featured/sasw.png" },
  { name: "Care Corner Singapore", src: "/landing/featured/carecorner.png" },
]

export function FeaturedSection() {
  const { t } = useLanguage()

  return (
    <section className="border-t border-neutral-200/60 bg-neutral-50 py-14 px-6">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-40px" }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
          {t.featured.heading}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-8 md:gap-x-8">
          {featuredLogos.map((logo) => (
            <img
              key={logo.name}
              src={logo.src}
              alt={logo.name}
              className={cn("w-auto object-contain transition-opacity duration-200", logo.name === "Better.sg" ? "h-10 md:h-11" : "h-14 md:h-16")}
              loading="lazy"
            />
          ))}
        </div>

        <div className="mt-10 pt-10 border-t border-neutral-100">
          <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
            {t.featured.partnersHeading}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
            {partnerLogos.map((logo) => (
              <img
                key={logo.name}
                src={logo.src}
                alt={logo.name}
                className="h-14 md:h-16 w-auto object-contain transition-opacity duration-200"
                loading="lazy"
              />
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  )
}
