"use client"

import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/landing/ui/button"
import { agencies } from "@/data/landing-agencies"
import type { Agency } from "@/data/landing-agencies"
import { useLanguage } from "@/lib/landing-i18n"

// Build 3 rows from the 24 agencies (8 per row), tripled for overflow
const rows: Agency[][] = [
  agencies.slice(0, 8),
  agencies.slice(8, 16),
  agencies.slice(16, 24),
]

// Pre-compute tripled rows at module level (static data, no need to recompute per render)
const tripledRows = rows.map((row) => [...row, ...row, ...row])

// Horizontal offsets to stagger each row for visual variety
const rowOffsets = ["3%", "-2%", "1%", "-3%", "2%", "-1%"]

export function AgenciesSection() {
  const { t } = useLanguage()

  return (
    <section id="about" className="py-10 px-6 bg-neutral-50">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white overflow-hidden pt-16 pb-0">
        {/* Header content */}
        <div className="text-center px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="font-landing-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
              {t.agencies.heading.split("\n").map((line, i, arr) => (
                <span key={i}>
                  {line}
                  {i < arr.length - 1 && <>{" "}<br className="hidden sm:inline" /></>}
                </span>
              ))}
            </h2>
            <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
              {t.agencies.subtitle}
            </p>
            <Button
              size="lg"
              className="mt-7 rounded-full bg-neutral-900 hover:bg-neutral-800 text-white px-8 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200"
              asChild
            >
              <a href="/">
                {t.agencies.cta} <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </motion.div>
        </div>

        {/* Static agency pills — diamond fade using radial mask */}
        <div
          className="mt-10 overflow-hidden"
          style={{
            maskImage: "radial-gradient(ellipse 70% 65% at 50% 50%, black 20%, transparent 75%)",
            WebkitMaskImage: "radial-gradient(ellipse 70% 65% at 50% 50%, black 20%, transparent 75%)",
          }}
        >
          <div className="flex flex-col items-center gap-4 py-4">
            {tripledRows.map((tripled, i) => (
                <div
                  key={i}
                  className="flex gap-4"
                  style={{ transform: `translateX(${rowOffsets[i]})` }}
                >
                  {tripled.map((agency, j) => (
                    <div
                      key={`${agency.shortName}-${j}`}
                      className="flex shrink-0 items-center gap-3 rounded-full border border-neutral-200/60 bg-neutral-50 px-4 py-2.5"
                    >
                      <img
                        src={agency.logo}
                        alt={agency.name}
                        className="h-9 w-9 rounded-full object-cover bg-neutral-100"
                        loading="lazy"
                      />
                      <span className="text-[15px] font-medium text-neutral-700 whitespace-nowrap">
                        {agency.shortName}
                      </span>
                    </div>
                  ))}
                </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
