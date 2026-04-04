"use client"

import { motion } from "framer-motion"
import { useLanguage } from "@/lib/landing-i18n"
import { cn } from "@/lib/utils"

const featuredLogos = [
  { name: "Channel NewsAsia", src: "/featured/cna-logo.fe6e55ec.svg" },
  { name: "Lianhe Zaobao", src: "/featured/lianhe-zaobao-logo.c41c922e.svg" },
  { name: "Money FM", src: "/featured/moneyfm-logo.c4778b09.svg" },
  { name: "Better.sg", src: "/featured/bettersg-logo.svg" },
  { name: "Sengkang Town Council", src: "/featured/sengkang-logo.4fef7e5f.svg" },
  { name: "Hatch", src: "/featured/hatch-logo.png" },
]

const partnerLogos = [
  { name: "Singapore Association of Social Workers", src: "/featured/sasw.a489ae5f.png" },
  { name: "Care Corner Singapore", src: "/featured/carecorner.cf5eba1a.png" },
]

export function FeaturedSection() {
  const { t } = useLanguage()

  return (
    <section className="border-t border-[#e8eef6] bg-white py-14 px-6">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-40px" }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-center text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-10">
          {t.featured.heading}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-8 md:gap-x-8">
          {featuredLogos.map((logo) => (
            <img
              key={logo.name}
              src={logo.src}
              alt={logo.name}
              className={cn("w-auto object-contain", logo.name === "Better.sg" ? "h-10 md:h-11" : "h-14 md:h-16")}
              loading="lazy"
            />
          ))}
        </div>
        <div className="mt-10 pt-10 border-t border-[#eef2f7]">
          <p className="text-center text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-10">
            {t.featured.partnersHeading}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
            {partnerLogos.map((logo) => (
              <img
                key={logo.name}
                src={logo.src}
                alt={logo.name}
                className="h-14 md:h-16 w-auto object-contain"
                loading="lazy"
              />
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  )
}
