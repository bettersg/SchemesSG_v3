"use client"

import { motion, useReducedMotion } from "framer-motion"
import { Search, SlidersHorizontal, Sparkles, Globe, UserCheck } from "lucide-react"
import { SectionWrapper } from "@/components/landing/shared/SectionWrapper"
import { useLanguage } from "@/lib/landing-i18n"
import Gravity, { MatterBody } from "../ui/gravity"
import { cn } from "@/lib/landing-utils"

/* ------------------------------------------------------------------ */
/*  Decorative illustration components for each bento card             */
/* ------------------------------------------------------------------ */

function SearchIllustration() {
  return (
    <div className="relative rounded-xl bg-neutral-50 border border-neutral-100 p-4 overflow-hidden">
      {/* Mock browser chrome */}
      <div className="flex items-center gap-1.5 mb-3">
        <div className="h-2 w-2 rounded-full bg-neutral-300" />
        <div className="h-2 w-2 rounded-full bg-neutral-200" />
        <div className="h-2 w-2 rounded-full bg-neutral-200" />
        <div className="ml-3 h-3 w-32 rounded-full bg-neutral-100" />
      </div>
      {/* Search bar */}
      <div className="rounded-lg bg-white border border-neutral-200 p-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Search className="h-3.5 w-3.5 text-neutral-400" />
          <span className="text-xs text-neutral-500">I&rsquo;m a single mother looking for financial aid...</span>
        </div>
      </div>
      {/* Result cards */}
      <div className="mt-3 space-y-2">
        <div className="rounded-lg bg-white border border-neutral-200 p-3 shadow-sm">
          <div className="flex items-center gap-2">
            <img src="/landing/logos/msf.jpg" alt="" className="h-6 w-6 rounded-full" />
            <div>
              <p className="text-xs font-semibold text-neutral-800">ComCare Short-to-Medium-Term</p>
              <p className="text-[10px] text-neutral-400">Ministry of Social and Family Development</p>
            </div>
          </div>
          <p className="mt-1.5 text-[10px] text-neutral-500 leading-relaxed">Financial assistance for lower-income families facing difficulties...</p>
          <div className="mt-2 flex gap-1.5">
            <span className="rounded-full bg-amber-50 border border-amber-200 px-2 py-0.5 text-[9px] font-medium text-amber-700">Financial Aid</span>
            <span className="rounded-full bg-neutral-50 border border-neutral-200 px-2 py-0.5 text-[9px] font-medium text-neutral-500">Families</span>
            <span className="rounded-full bg-neutral-50 border border-neutral-200 px-2 py-0.5 text-[9px] font-medium text-neutral-500">Monthly</span>
          </div>
        </div>
        <div className="rounded-lg bg-white/60 border border-neutral-100 p-3">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-neutral-100" />
            <div className="h-2.5 w-28 rounded bg-neutral-100" />
          </div>
          <div className="mt-2 h-2 w-full rounded bg-neutral-50" />
          <div className="mt-1 h-2 w-3/4 rounded bg-neutral-50" />
        </div>
      </div>
    </div>
  )
}

function DatabaseIllustration() {
  const shouldReduceMotion = useReducedMotion()
  const cards = [
    {
      posStyle: {
        top: '0%',
        left: '10%',
        rotate: '-6deg'
      },
      text: 'Healthcare',
      textStyle: 'bg-blue-100 text-blue-600'
    }, {
      posStyle: {
        top: '0%',
        left: '50%',
        rotate: '4deg'
      },
      text: 'Education',
      textStyle: 'bg-amber-100 text-amber-600'
    }, {
      posStyle: {
        top: '34%',
        left: '2%',
        rotate: '2deg'
      },
      text: 'Financial Aid',
      textStyle: 'bg-red-100 text-red-600'
    }, {
      posStyle: {
        top: '36%',
        left: '56%',
        rotate: '-3deg'
      },
      text: 'Disability',
      textStyle: 'bg-purple-100 text-purple-600'
    }, {
      posStyle: {
        top: '70%',
        left: '50%',
        rotate: '5deg'
      },
      text: 'Childcare',
      textStyle: 'bg-rose-100 text-rose-600'
    }, {
      posStyle: {
        top: '70%',
        left: '10%',
        rotate: '-2deg'
      },
      text: 'Eldercare',
      textStyle: 'bg-teal-100 text-teal-600'
    }
  ]
  if (shouldReduceMotion) {
    return (

      <div className="relative flex items-center justify-center py-4">
        {/* Scattered scheme category cards */}
        <div className="relative h-40 w-full">
          {cards.map(card => (
            <div key={card.text} className={cn("absolute rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-sm")} style={{...card.posStyle}}>
            <div className="flex items-center gap-1.5">
              <div className={cn("w-5 h-5 sm:w-8 sm:h-8 rounded bg-blue-100 flex items-center justify-center text-[8px] sm:text-[12px] font-bold", card.textStyle)}>{card.text.charAt(0)}</div>
              <span className="text-[10px] sm:text-[14px] font-medium text-neutral-700">{card.text}</span>
            </div>
          </div>
          ))}
        </div>
      </div>
    )
  } else {
    return (
      <Gravity gravity={{ x: 0, y: 1 }} className="w-full h-full relative">
        {cards.map(card => (
          <MatterBody
          matterBodyOptions={{ friction: 0.5, restitution: 0.2 }}
          x={card.posStyle.left}
          y={card.posStyle.top}
          key={card.text}
        >
          <div className={cn("rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-sm")}>
            <div className="flex items-center gap-1.5">
              <div className={cn("w-5 h-5 sm:w-8 sm:h-8 rounded bg-blue-100 flex items-center justify-center text-[8px] sm:text-[12px] font-bold", card.textStyle)}>{card.text.charAt(0)}</div>
              <span className="text-[10px] sm:text-[14px] font-medium text-neutral-700">{card.text}</span>
            </div>
          </div>
        </MatterBody>
        ))}
      </Gravity>
    )
  }
}

function FilterIllustration() {
  return (
    <div className="rounded-xl bg-neutral-50 border border-neutral-100 p-4 space-y-4">
      {/* Agency logo row + filter */}
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          <img src="/landing/logos/hdb.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm" />
          <img src="/landing/logos/MOH.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
          <img src="/landing/logos/cpf.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
          <img src="/landing/logos/msf.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
        </div>
        <div className="relative">
          <div className="flex items-center gap-1.5 rounded-full border border-neutral-200 bg-white px-3 py-1.5 shadow-sm">
            <SlidersHorizontal className="h-3.5 w-3.5 text-neutral-500" />
            <span className="text-xs font-medium text-neutral-600">Filter</span>
          </div>
          {/* Mouse cursor */}
          <svg className="absolute -bottom-2 -right-1 h-4 w-4 text-neutral-700 drop-shadow-sm" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 1l5.5 14 2.2-5.8L14.5 7z" />
          </svg>
        </div>
      </div>
      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 shadow-sm">
          <img src="/landing/logos/sgenable.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-neutral-700">Disability Support</span>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 shadow-sm">
          <img src="/landing/logos/aic.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-neutral-700">Eldercare</span>
        </div>
      </div>
      {/* Tags row */}
      <div className="flex items-center gap-4 text-xs text-neutral-500">
        <span>Singapore</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-400" />
          Eligible
        </span>
        <Sparkles className="h-3.5 w-3.5 text-neutral-300" />
      </div>
    </div>
  )
}

function SuggestSchemeIllustration() {
  return (
    <div className="relative rounded-xl bg-neutral-50 border border-neutral-100 p-3.5 overflow-hidden">
      {/* Step 1: User submits URL */}
      <div className="flex items-center gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-neutral-200 text-neutral-500 text-[10px] font-bold">1</div>
        <div className="flex-1 rounded-lg bg-white border border-neutral-200 px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <Globe className="h-3 w-3 shrink-0 text-neutral-400" />
            <span className="text-[10px] text-neutral-500 truncate">https://gov.sg/schemes/new-grant</span>
          </div>
        </div>
      </div>

      <div className="ml-3 border-l-2 border-dashed border-neutral-200 h-3" />

      {/* Step 2: AI agents extract */}
      <div className="flex items-center gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">2</div>
        <div className="flex-1 rounded-lg bg-white border border-neutral-200 px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 shrink-0 text-blue-600" />
            <span className="text-[10px] text-neutral-700 font-medium">AI extracting scheme details</span>
          </div>
          <div className="mt-1.5 flex gap-1">
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[8px] text-neutral-500">Eligibility</span>
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[8px] text-neutral-500">Benefits</span>
            <span className="rounded bg-neutral-100 px-1.5 py-0.5 text-[8px] text-neutral-500">Agency</span>
          </div>
        </div>
      </div>

      <div className="ml-3 border-l-2 border-dashed border-neutral-200 h-3" />

      {/* Step 3: Slack approval */}
      <div className="flex items-start gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-neutral-800 text-white text-[10px] font-bold">3</div>
        <div className="flex-1 rounded-lg bg-white border border-neutral-200 px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5 mb-1.5">
            <svg className="h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none">
              <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm6.33 2.521a2.528 2.528 0 0 1 2.52-2.521A2.528 2.528 0 0 1 20.206 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.52V8.834zm-1.272 0a2.528 2.528 0 0 1-2.52 2.521 2.527 2.527 0 0 1-2.521-2.521V2.522A2.527 2.527 0 0 1 11.372 0a2.528 2.528 0 0 1 2.52 2.522v6.312zm-2.52 6.33a2.528 2.528 0 0 1 2.52 2.52 2.527 2.527 0 0 1-2.52 2.522 2.527 2.527 0 0 1-2.521-2.522v-2.52h2.52zm0-1.272a2.528 2.528 0 0 1-2.521-2.52 2.528 2.528 0 0 1 2.521-2.521h6.312A2.528 2.528 0 0 1 24 11.372a2.528 2.528 0 0 1-2.522 2.52h-6.312z" fill="#E01E5A"/>
            </svg>
            <span className="text-[10px] font-semibold text-neutral-700">#scheme-reviews</span>
          </div>
          <div className="rounded bg-neutral-50 border border-neutral-100 px-2 py-1.5">
            <p className="text-[10px] text-neutral-600"><span className="font-semibold">New Housing Grant 2025</span> — HDB</p>
            <div className="mt-1.5 flex gap-1.5">
              <span className="flex items-center gap-1 rounded bg-blue-600 px-2 py-0.5 text-[9px] font-semibold text-white">
                <UserCheck className="h-2.5 w-2.5" /> Approve
              </span>
              <span className="rounded bg-white border border-neutral-200 px-2 py-0.5 text-[9px] text-neutral-500">Reject</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main section                                                       */
/* ------------------------------------------------------------------ */

export function FeaturesSection() {

  const { t } = useLanguage()

  return (
    <SectionWrapper id="features" className="bg-neutral-50 overflow-hidden">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-landing-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            {t.features.heading}
          </h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            {t.features.subtitle}
          </p>
        </motion.div>
      </div>

      {/* Bento grid — two flex columns */}
      <div className="relative mt-16 mx-auto max-w-5xl grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Background gradient glows */}
        <div className="pointer-events-none absolute z-0 -top-40 -left-20 h-[600px] w-[600px] rounded-full bg-amber-200 opacity-40 blur-[150px]" />
        <div className="pointer-events-none absolute z-0 top-1/4 -right-10 h-[500px] w-[500px] rounded-full bg-blue-200 opacity-30 blur-[130px]" />
        <div className="pointer-events-none absolute z-0 -bottom-20 left-1/3 h-[500px] w-[500px] rounded-full bg-amber-100 opacity-40 blur-[120px]" />
        {/* Left column */}
        <div className="relative z-10 flex flex-col gap-5">
          {/* Card 1 — AI-Powered Search */}
          <motion.div
            className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5 }}
          >
            <SearchIllustration />
            <h3 className="mt-5 text-lg font-bold tracking-tight">
              {t.features.cards.search.title}
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              {t.features.cards.search.description}
            </p>
          </motion.div>

          {/* Card 4 — Eligibility Matching */}
          <motion.div
            className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <SuggestSchemeIllustration />
            <h3 className="mt-5 text-lg font-bold tracking-tight">
              {t.features.cards.suggest.title}
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              {t.features.cards.suggest.description}
            </p>
          </motion.div>
        </div>

        {/* Right column */}
        <div className="relative z-10 flex flex-col gap-5">
          {/* Card 2 — Comprehensive Database */}
          <motion.div
            className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="w-full h-[200px] sm:h-[300px] relative">
              <DatabaseIllustration />
            </div>
            <h3 className="mt-4 text-lg font-bold tracking-tight">
              {t.features.cards.database.title}
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              {t.features.cards.database.description}
            </p>
          </motion.div>

          {/* Card 3 — Smart Filtering */}
          <motion.div
            className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.15 }}
          >
            <FilterIllustration />
            <h3 className="mt-4 text-lg font-bold tracking-tight">
              {t.features.cards.filter.title}
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              {t.features.cards.filter.description}
            </p>
          </motion.div>

        </div>
      </div>
    </SectionWrapper>
  )
}
