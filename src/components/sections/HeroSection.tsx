import { useState } from "react"
import { motion } from "motion/react"
import { Search, ArrowRight, Sparkles } from "lucide-react"
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
    <section className="relative min-h-[100svh] flex items-center overflow-hidden bg-neutral-50 grain-overlay">
      {/* Gradient glow orbs */}
      <div className="pointer-events-none absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-lime-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-10%] right-[5%] h-[500px] w-[500px] rounded-full bg-lime-200/15 blur-[100px]" />

      <div className="relative mx-auto w-full max-w-7xl grid grid-cols-1 lg:grid-cols-[200px_1fr_200px] gap-8 px-6 py-24 lg:py-20">
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
          {/* Floating 3D icon */}
          <motion.div
            className="animate-float mb-6 relative z-10"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="relative">
              <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-2xl bg-gradient-to-br from-sky-300 to-sky-500 shadow-xl shadow-sky-400/20 flex items-center justify-center rotate-[-8deg]">
                <Sparkles className="h-7 w-7 sm:h-9 sm:w-9 text-white" strokeWidth={1.5} />
              </div>
              <div className="absolute -bottom-1 -right-1 h-5 w-5 sm:h-6 sm:w-6 rounded-lg bg-neutral-200 shadow-sm rotate-12" />
            </div>
          </motion.div>

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
            <div className="relative flex items-center rounded-full bg-white border border-neutral-300 shadow-[0_4px_24px_rgba(0,0,0,0.08)] hover:shadow-[0_6px_32px_rgba(0,0,0,0.12)] transition-shadow duration-300 focus-within:ring-2 focus-within:ring-lime-400/50 focus-within:border-lime-400">
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
                className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-full bg-lime-400 hover:bg-lime-500 text-neutral-900 transition-colors duration-200 cursor-pointer shadow-sm"
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
