"use client"

import { useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { NumberTicker } from "@/components/magicui/number-ticker"
import { BlurFade } from "@/components/magicui/blur-fade"

/* ── Stats data ─────────────────────────────────────────── */
const STATS = [
  { value: 500, suffix: "+", label: "Social schemes listed" },
  { value: 200, suffix: "+", label: "Partner agencies" },
  { value: 1200, suffix: "+", label: "Monthly users" },
  { value: 100, suffix: "%", label: "Anonymous & private" },
]

/* ── How it works data ──────────────────────────────────── */
const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M3 5h16M3 9h10M3 13h13M3 17h8" stroke="#185FA5" strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    ),
    bg: "bg-[#E6F1FB]",
    title: "Describe your situation",
    desc: "Our AI understands your context and finds what kind of support you need.",
    step: 1,
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M11 3L13.5 8.5L19.5 9.5L15 14L16 20L11 17L6 20L7 14L2.5 9.5L8.5 8.5L11 3Z" stroke="#BA7517" strokeWidth="1.8" strokeLinejoin="round"/>
      </svg>
    ),
    bg: "bg-[#FAEEDA]",
    title: "Get matched schemes",
    desc: "A personalised list of schemes with eligibility, benefits, and how to apply",
    step: 2,
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M5 17L17 5M12 5h5v5" stroke="#534AB7" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    bg: "bg-[#EEEDFE]",
    title: "Take action directly",
    desc: "Contact agencies, get referral guidance, or share details with a social worker",
    step: 3,
  },
]

/* ── Animated timeline dot ──────────────────────────────── */
function TimelineDot({ active, completed }: { active: boolean; completed: boolean }) {
  return (
    <div className="relative flex items-center justify-center w-8 h-8 flex-shrink-0 z-10">
      <motion.div
        className="absolute inset-0 rounded-full"
        animate={{
          backgroundColor: completed || active ? "#185FA5" : "#E6F1FB",
          scale: active ? 1.15 : 1,
        }}
        transition={{ duration: 0.3 }}
      />
      <motion.div
        className="relative z-10 w-3 h-3 rounded-full"
        animate={{ backgroundColor: completed || active ? "#fff" : "#B5D4F4" }}
        transition={{ duration: 0.3 }}
      />
    </div>
  )
}

/* ── Card hover effect ──────────────────────────────────── */
function HoverCard({
  feature,
//   index,
//   hoveredIndex,
//   onHover,
//   onLeave,
}: {
  feature: typeof FEATURES[0]
//   index: number
//   hoveredIndex: number | null
//   onHover: (i: number) => void
//   onLeave: () => void
}) {
//   const isHovered = hoveredIndex === index

  return (
    <div
      className="relative cursor-pointer"
    //   onMouseEnter={() => onHover(index)}
    //   onMouseLeave={onLeave}
    >
      {/* <AnimatePresence>
        {isHovered && (
          <motion.div
            layoutId="hoverBg"
            className="absolute inset-0 rounded-2xl bg-[#E6F1FB] border-2 border-[#B5D4F4]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.15 } }}
            exit={{ opacity: 0, transition: { duration: 0.15, delay: 0.1 } }}
          />
        )}
      </AnimatePresence> */}
      <div className="h-full relative z-10 bg-white border-2 border-[#eef2f7] rounded-2xl p-6 overflow-hidden transition-colors duration-200 group-hover:border-transparent">
        {/* Coloured top accent */}
        <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#378ADD] to-[#7F77DD] rounded-t-2xl" />
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${feature.bg}`}>
          {feature.icon}
        </div>
        <h3 className="font-[var(--font-head)] text-[15px] font-semibold text-[#042C53] mb-2">
          {feature.title}
        </h3>
        <p className="text-sm text-[#5F5E5A] leading-relaxed">{feature.desc}</p>
      </div>
    </div>
  )
}

/* ── Mobile animated timeline ───────────────────────────── */
function AnimatedTimeline({ features }: { features: typeof FEATURES }) {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null)

  return (
    <div className="flex flex-col gap-0">
      {features.map((f, i) => {
        const isActive = hoveredStep === i
        const isCompleted = hoveredStep !== null && i < hoveredStep
        const isLast = i === features.length - 1

        return (
          <div
            key={i}
            className="flex gap-4 cursor-pointer"
            onMouseEnter={() => setHoveredStep(i)}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Left: connector + dot */}
            <div className="flex flex-col items-center">
              <TimelineDot active={isActive} completed={isCompleted} />
              {!isLast && (
                <motion.div
                  className="w-[2px] flex-1 my-1 rounded-full origin-top"
                  animate={{
                    backgroundColor: isCompleted ? "#185FA5" : "#E6F1FB",
                    scaleY: 1,
                  }}
                  transition={{ duration: 0.35 }}
                  style={{ minHeight: 32 }}
                />
              )}
            </div>

            {/* Right: card */}
            <div className="pb-6 flex-1">
              <motion.div
                className="rounded-2xl border-2 p-5 overflow-hidden relative"
                animate={{
                  borderColor: isActive ? "#378ADD" : "#eef2f7",
                  backgroundColor: isActive ? "#f0f6ff" : "#ffffff",
                }}
                transition={{ duration: 0.25 }}
              >
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#378ADD] to-[#7F77DD] rounded-t-2xl" />
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-3 ${f.bg}`}>
                  {f.icon}
                </div>
                <h3 className="font-[var(--font-head)] text-[15px] font-semibold text-[#042C53] mb-1">
                  {f.title}
                </h3>
                <p className="text-sm text-[#5F5E5A] leading-relaxed">{f.desc}</p>
              </motion.div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

/* ── Main export ─────────────────────────────────────────── */
export function StatsAndHowItWorksSection() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  return (
    <>
      {/* ── Stats bar ── */}
      <div className="bg-white border-b border-[#e8eef6]">
        <div className="max-w-[960px] mx-auto grid grid-cols-2 sm:grid-cols-4">
          {STATS.map((s, i) => (
            <BlurFade key={s.label} delay={i * 0.1} inView>
              <div className="py-6 px-4 text-center border-r last:border-r-0 border-[#e8eef6] sm:py-8 h-full">
                <div className="font-[var(--font-head)] text-3xl font-extrabold text-[#185FA5]">
                  <NumberTicker value={s.value} delay={i * 0.1} />
                  {s.suffix}
                </div>
                <div className="text-xs text-[#B4B2A9] mt-1">{s.label}</div>
              </div>
            </BlurFade>
          ))}
        </div>
      </div>

      {/* ── How it works ── */}
      <section className="bg-[#f7f9fc] py-16 px-4 sm:px-8 lg:px-16">
        <div className="max-w-[960px] mx-auto">
          <BlurFade inView delay={0}>
            <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">
              How it works
            </p>
            <h2 className="font-[var(--font-head)] text-3xl sm:text-4xl font-bold text-[#042C53] mb-3 leading-tight">
              One conversation.<br />The right schemes.
            </h2>
            <p className="text-[#5F5E5A] text-base mb-10 max-w-[500px] leading-relaxed">
              Tell our AI what you&apos;re going through. It finds the most relevant support and helps
              you understand how to access it.
            </p>
          </BlurFade>

          {/* Desktop: card hover effect grid */}
          <div className="hidden sm:grid grid-cols-3 gap-5 relative group">
            {FEATURES.map((f, i) => (
              <HoverCard
                key={f.title}
                feature={f}
                // index={i}
                // hoveredIndex={hoveredIndex}
                // onHover={setHoveredIndex}
                // onLeave={() => setHoveredIndex(null)}
              />
            ))}
          </div>

          {/* Mobile: animated timeline */}
          <div className="sm:hidden">
            <AnimatedTimeline features={FEATURES} />
          </div>
        </div>
      </section>
    </>
  )
}
