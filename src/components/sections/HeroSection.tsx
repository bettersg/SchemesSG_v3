import { useState } from "react"
import { motion } from "motion/react"
import { Search, ArrowRight, ArrowUpRight } from "lucide-react"
import { ScrollingColumn } from "@/components/shared/ScrollingColumn"
import { ScrollingLogoColumn } from "@/components/shared/ScrollingLogoColumn"
import { heroContent, schemeCategories } from "@/data/content"
import { agencies } from "@/data/agencies"

const examplePrompt = "I'm a single parent looking for financial assistance..."

export function HeroSection() {
  const [query, setQuery] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const searchQuery = query || examplePrompt
    window.location.href = `https://schemes.sg/search?q=${encodeURIComponent(searchQuery)}`
  }

  return (
    <section className="relative min-h-0 lg:min-h-[100svh] flex items-center overflow-hidden bg-neutral-50 grain-overlay">
      {/* Gradient glow orbs */}
      <div className="pointer-events-none absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-amber-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-10%] right-[5%] h-[500px] w-[500px] rounded-full bg-blue-200/10 blur-[100px]" />

      <div className="relative mx-auto w-full max-w-7xl grid grid-cols-1 lg:grid-cols-[200px_1fr_200px] gap-8 px-6 pt-28 pb-16 lg:py-20">
        {/* Left scrolling column — scheme categories */}
        <div className="hidden lg:flex items-center">
          <ScrollingColumn
            items={schemeCategories}
            direction="up"
            highlightIndex={3}
            speed={28}
          />
        </div>

        {/* Center content */}
        <div className="flex flex-col items-center justify-center text-center">
          {/* Volunteer banner */}
          <motion.a
            href="https://better.sg"
            target="_blank"
            rel="noopener noreferrer"
            className="mb-8 inline-flex items-center gap-3 rounded-full bg-neutral-900 px-3.5 py-1 text-xs text-neutral-300 hover:bg-neutral-800 transition-colors duration-200 cursor-pointer"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <span className="leading-none">Built by volunteers at</span>
            <img src="/featured/bettersg-logo.a549b628.svg" alt="better.sg" className="h-6 w-auto brightness-0 invert -mx-1.5 translate-y-[1px]" />
            <span className="h-3 w-px bg-neutral-700 shrink-0" />
            <span className="font-medium text-white leading-none flex items-center gap-1">
              Get involved <ArrowUpRight className="h-3 w-3" />
            </span>
          </motion.a>

          {/* Headline */}
          <motion.h1
            className="font-serif text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl lg:text-[4.5rem] xl:text-[5rem]"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            {heroContent.headline.split("\n").map((line, i) => (
              <span key={i}>
                {line}
                {i < heroContent.headline.split("\n").length - 1 && <br />}
              </span>
            ))}
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-neutral-500"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {heroContent.subtitle}
          </motion.p>

          {/* Search bar */}
          <motion.form
            onSubmit={handleSubmit}
            className="mt-8 w-full max-w-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
          >
            <div className="relative flex items-center rounded-full bg-white border border-neutral-300 shadow-[0_4px_24px_rgba(0,0,0,0.08)] hover:shadow-[0_6px_32px_rgba(0,0,0,0.12)] transition-shadow duration-300 focus-within:ring-2 focus-within:ring-amber-400/50 focus-within:border-amber-400">
              <Search className="absolute left-5 h-5 w-5 text-neutral-500 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={examplePrompt}
                className="w-full bg-transparent py-4 pl-13 pr-14 text-[15px] text-neutral-800 placeholder:text-neutral-500 focus:outline-none rounded-full"
              />
              <button
                type="submit"
                className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 transition-colors duration-200 cursor-pointer shadow-sm"
                aria-label="Search"
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-3 text-xs text-neutral-400">
              Try: &ldquo;healthcare subsidies for seniors&rdquo; or &ldquo;education grants for low-income families&rdquo;
            </p>
          </motion.form>
        </div>

        {/* Right scrolling column — agency logos */}
        <div className="hidden lg:flex items-center justify-end">
          <ScrollingLogoColumn
            agencies={agencies}
            speed={32}
          />
        </div>
      </div>
    </section>
  )
}
