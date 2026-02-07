import { motion } from "motion/react"
import { ArrowRight, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollingColumn } from "@/components/shared/ScrollingColumn"
import { ScrollingLogoColumn } from "@/components/shared/ScrollingLogoColumn"
import { heroContent, schemeCategories } from "@/data/content"
import { agencies } from "@/data/agencies"

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-neutral-50 grain-overlay">
      {/* Gradient glow orbs */}
      <div className="pointer-events-none absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-lime-300/10 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-[-10%] right-[5%] h-[500px] w-[500px] rounded-full bg-lime-200/15 blur-[100px]" />

      <div className="relative mx-auto w-full max-w-7xl grid grid-cols-1 lg:grid-cols-[200px_1fr_200px] gap-8 px-6 py-32 lg:py-24">
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
            className="animate-float mb-8 relative z-10"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="relative">
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-sky-300 to-sky-500 shadow-xl shadow-sky-400/20 flex items-center justify-center rotate-[-8deg]">
                <Sparkles className="h-9 w-9 text-white" strokeWidth={1.5} />
              </div>
              <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-lg bg-neutral-200 shadow-sm rotate-12" />
            </div>
          </motion.div>

          {/* Headline */}
          <motion.h1
            className="font-serif text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-[5rem] xl:text-[5.5rem]"
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
            className="mt-7 max-w-xl text-lg leading-relaxed text-neutral-500"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {heroContent.subtitle}
          </motion.p>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
          >
            <Button
              size="lg"
              className="mt-9 rounded-full bg-lime-400 hover:bg-lime-500 text-neutral-900 px-9 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200 border-0"
              asChild
            >
              <a href="https://schemes.sg">
                {heroContent.cta}
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
          </motion.div>
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
