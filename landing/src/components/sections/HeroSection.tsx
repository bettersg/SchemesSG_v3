"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { ScrollingColumn } from "@/components/shared/ScrollingColumn"
import { ScrollingLogoColumn } from "@/components/shared/ScrollingLogoColumn"
import { useLanguage } from "@/lib/landing-i18n"
import { agencies } from "@/data/landing-agencies"

const heroAgencies = agencies.slice(0, 12)

const CATEGORY_CHIPS = [
  { label: "Financial Aid", emoji: "💰" },
  { label: "Healthcare", emoji: "🏥" },
  { label: "Mental Health", emoji: "🧠" },
  { label: "Family Support", emoji: "👨‍👩‍👧" },
  { label: "Housing", emoji: "🏠" },
  { label: "Employment", emoji: "💼" },
  { label: "Food Assistance", emoji: "🍚" },
  { label: "Education", emoji: "📚" },
]

export function HeroSection() {
  const { t } = useLanguage()
  const [query, setQuery] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const searchQuery = query || t.hero.searchPlaceholder
    window.location.href = `/?q=${encodeURIComponent(searchQuery)}`
  }

  function handleChipClick(label: string) {
    const q = `I need ${label.toLowerCase()} support`
    window.location.href = `/?q=${encodeURIComponent(q)}`
  }

  return (
    <section className="relative min-h-0 lg:min-h-[100svh] flex items-center overflow-hidden bg-[#f0f6ff] grain-overlay">
      {/* Gradient glow orbs — brand colours */}
      <div className="pointer-events-none absolute bottom-[10%] left-[10%] h-[600px] w-[600px] rounded-full bg-[#EF9F27]/10 blur-[120px]" />
      <div className="pointer-events-none absolute top-[10%] right-[5%] h-[600px] w-[600px] rounded-full bg-[#185FA5]/15 blur-[120px]" />

      <div className="relative mx-auto w-full max-w-7xl grid grid-cols-1 lg:grid-cols-[200px_1fr_200px] gap-8 px-6 pt-28 pb-16 lg:py-20">
        {/* Left scrolling column */}
        <div className="hidden lg:flex items-center">
          <ScrollingColumn
            items={t.schemeCategories}
            direction="up"
            highlightIndex={3}
            speed={28}
          />
        </div>

        {/* Center content */}
        <div className="flex flex-col items-center justify-center text-center">
          {/* Live badge */}
          <motion.div
            className="inline-flex items-center gap-2 bg-[#E6F1FB] border border-[#B5D4F4] rounded-full px-3 py-1.5 text-xs font-semibold text-[#185FA5] mb-6"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#1D9E75] animate-pulse" />
            {t.hero.searchHint}
          </motion.div>

          {/* Headline */}
          <motion.h1
            className="font-[var(--font-head)] text-4xl font-extrabold leading-[1.08] tracking-tight text-[#042C53] sm:text-5xl lg:text-[4.5rem] xl:text-[5rem]"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            {t.hero.headline.split("\n").map((line, i, arr) => (
              <span key={i}>
                {i === 1 ? (
                  <span className="text-[#185FA5]">{line}</span>
                ) : (
                  line
                )}
                {i < arr.length - 1 && <br />}
              </span>
            ))}
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-[#5F5E5A]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {t.hero.subtitle}
          </motion.p>

          {/* Search bar */}
          <motion.form
            onSubmit={handleSubmit}
            className="mt-8 w-full max-w-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
          >
            <div className="relative flex items-center rounded-2xl bg-white border-2 border-[#d0e4f7] shadow-[0_4px_24px_rgba(24,95,165,0.10)] hover:shadow-[0_6px_32px_rgba(24,95,165,0.16)] transition-shadow duration-300 focus-within:border-[#378ADD]">
              <svg className="absolute left-4 shrink-0" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="7" cy="7" r="5.5" stroke="#B4B2A9" strokeWidth="1.5"/>
                <path d="M11 11L14.5 14.5" stroke="#B4B2A9" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t.hero.searchPlaceholder}
                className="w-full bg-transparent py-4 pl-12 pr-16 text-[15px] text-[#444441] placeholder:text-[#B4B2A9] focus:outline-none rounded-2xl"
              />
              <button
                type="submit"
                className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-xl bg-[#EF9F27] hover:bg-[#BA7517] text-white transition-colors duration-200 cursor-pointer shadow-sm"
                aria-label={t.a11y.search}
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </motion.form>

          {/* Category chips */}
          <motion.div
            className="mt-5 flex flex-wrap gap-2 justify-center"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            {CATEGORY_CHIPS.map((c) => (
              <button
                key={c.label}
                onClick={() => handleChipClick(c.label)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border-[1.5px] border-[#e0eaf5] rounded-full text-xs font-medium text-[#5F5E5A] hover:border-[#B5D4F4] hover:text-[#185FA5] hover:bg-[#E6F1FB] transition-all cursor-pointer"
              >
                <span>{c.emoji}</span> {c.label}
              </button>
            ))}
          </motion.div>
        </div>

        {/* Right scrolling column — agency logos */}
        <div className="hidden lg:flex items-center justify-end">
          <ScrollingLogoColumn
            agencies={heroAgencies}
            speed={32}
          />
        </div>
      </div>
    </section>
  )
}
