"use client"

import { motion } from "framer-motion"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { useLanguage } from "@/lib/landing-i18n"
import { MagicCard } from "@/components/magicui/magic-card"

export function TestimonialSection() {
  const { t } = useLanguage()

  return (
    <SectionWrapper className="bg-[#f7f9fc]">
      <div className="text-center mb-12">
        <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">
          What people say
        </p>
        <h2 className="font-[var(--font-head)] text-3xl font-bold tracking-tight text-[#042C53] md:text-4xl">
          Real stories, real impact
        </h2>
      </div>

      <div className="mx-auto max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
        {t.testimonials.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: index * 0.15 }}
          >
            {/* MagicCard wraps the content — gradient follows cursor in brand blue */}
            <MagicCard
              gradientColor="#E6F1FB"
              gradientSize={220}
              gradientOpacity={0.5}
              className="h-full rounded-2xl"
            >
              <div className="flex flex-col h-full rounded-2xl border border-[#e4edf7] bg-white p-8 lg:p-10 shadow-[0_2px_12px_rgba(4,44,83,0.06)] transition-shadow duration-300 hover:shadow-[0_4px_24px_rgba(24,95,165,0.12)]">
                {/* Amber quote mark */}
                <div className="text-[#EF9F27] text-4xl font-serif leading-none mb-4 select-none">
                  &ldquo;
                </div>

                <blockquote className="flex-1 font-[var(--font-head)] text-lg leading-relaxed tracking-tight text-[#042C53] lg:text-xl">
                  {item.quote}
                </blockquote>

                {/* Divider */}
                <div className="mt-6 mb-5 h-px bg-[#eef2f7]" />

                {/* Author */}
                <div className="flex items-center gap-3">
                  {item.avatar ? (
                    <img
                      src={item.avatar}
                      alt={item.author}
                      className="h-10 w-10 shrink-0 object-contain bg-white"
                    />
                  ) : (
                    <div className="h-10 w-10 shrink-0 rounded-full bg-[#EF9F27] flex items-center justify-center text-white font-bold text-sm shadow-sm select-none">
                      {item.author.charAt(0)}
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-semibold text-[#042C53]">{item.author}</p>
                    <p className="text-xs text-[#B4B2A9]">{item.role}</p>
                  </div>
                </div>
              </div>
            </MagicCard>
          </motion.div>
        ))}
      </div>
    </SectionWrapper>
  )
}
