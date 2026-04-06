"use client"

import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { agencies } from "@/data/landing-agencies"
import { useLanguage } from "@/lib/landing-i18n"
import { ScrollVelocityContainer, ScrollVelocityRow } from "@/components/magicui/scroll-based-velocity"

/* Two rows of agency pills for the Marquee */
const rowA = agencies.slice(0, 8)
const rowB = agencies.slice(8, 16)
const rowC = agencies.slice(16, 24)

function AgencyPill({ agency }: { agency: (typeof agencies)[0] }) {
  return (
    <div className="flex shrink-0 items-center gap-2.5 rounded-full border border-[#e4edf7] bg-[#f7fafd] px-4 py-2.5 mx-2">
      <img
        src={agency.logo}
        alt={agency.name}
        className="h-8 w-8 rounded-full object-cover bg-[#E6F1FB] flex-shrink-0"
        loading="lazy"
      />
      <span className="text-[13px] font-medium text-[#444441] whitespace-nowrap">
        {agency.shortName}
      </span>
    </div>
  )
}

export function AgenciesSection() {
  const { t } = useLanguage()

  return (
    <section id="about" className="py-10 px-6 bg-[#f7f9fc]">
      <div className="mx-auto max-w-5xl rounded-3xl bg-white overflow-hidden py-16 border border-[#e4edf7] shadow-[0_2px_24px_rgba(4,44,83,0.06)]">

        {/* Header */}
        <div className="text-center px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
          >
            <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">
              Agencies
            </p>
            <h2 className="font-[var(--font-head)] text-3xl font-bold tracking-tight text-[#042C53] md:text-4xl lg:text-[2.75rem]">
              {t.agencies.heading.split("\n").map((line, i, arr) => (
                <span key={i}>
                  {line}
                  {i < arr.length - 1 && (
                    <>{" "}<br className="hidden sm:inline" /></>
                  )}
                </span>
              ))}
            </h2>
            <p className="mt-4 text-[#5F5E5A] text-lg max-w-2xl mx-auto leading-relaxed">
              {t.agencies.subtitle}
            </p>
            <Button
              size="lg"
              className="mt-7 rounded-full bg-[#EF9F27] hover:bg-[#BA7517] text-white px-8 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200 border-0"
              asChild
            >
              <a href="/">
                {t.agencies.cta} <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </motion.div>
        </div>

        {/* ── Marquee rows (standard speed) ── */}
        <ScrollVelocityContainer
          className="mt-10 overflow-hidden flex flex-col gap-4"
          style={{
            maskImage:
              "linear-gradient(to right, transparent 0%, black 12%, black 88%, transparent 100%)",
            WebkitMaskImage:
              "linear-gradient(to right, transparent 0%, black 12%, black 88%, transparent 100%)",
          }}
        >
          {/* Row A — left */}
            <ScrollVelocityRow baseVelocity={5} direction={1}>
				{rowA.map((a) => (
				  <AgencyPill key={a.shortName} agency={a} />
				))}
			</ScrollVelocityRow >

          {/* Row B — right (reverse) */}
            <ScrollVelocityRow baseVelocity={5} direction={-1}>
				{rowB.map((a) => (
				  <AgencyPill key={a.shortName} agency={a} />
				))}
			</ScrollVelocityRow>

          {/* Row C — left */}
		  <ScrollVelocityRow baseVelocity={5} direction={1}>
				{rowC.map((a) => (
				  <AgencyPill key={a.shortName} agency={a} />
				))}
			</ScrollVelocityRow>
        </ScrollVelocityContainer>

        
      </div>
    </section>
  )
}
