"use client"

import { motion, useReducedMotion } from "framer-motion"
import { Search, SlidersHorizontal, Sparkles, Globe, UserCheck } from "lucide-react"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { useLanguage } from "@/lib/landing-i18n"
import Gravity, { MatterBody } from "./gravity"
import { cn } from "@/lib/utils"

/* ── Illustrations ────────────────────────────────────────── */

function SearchIllustration() {
  return (
    <div className="relative rounded-xl bg-[#f7fafd] border border-[#e4edf7] p-4 overflow-hidden">
      <div className="flex items-center gap-1.5 mb-3">
        <div className="h-2 w-2 rounded-full bg-[#D3D1C7]" />
        <div className="h-2 w-2 rounded-full bg-[#e0eaf5]" />
        <div className="h-2 w-2 rounded-full bg-[#e0eaf5]" />
        <div className="ml-3 h-3 w-32 rounded-full bg-[#e0eaf5]" />
      </div>
      <div className="rounded-xl bg-white border border-[#e0eaf5] p-3 shadow-sm">
        <div className="flex items-center gap-2">
          <Search className="h-3.5 w-3.5 text-[#B4B2A9]" />
          <span className="text-xs text-[#5F5E5A]">I&rsquo;m a single mother looking for financial aid...</span>
        </div>
      </div>
      <div className="mt-3 space-y-2">
        <div className="rounded-xl bg-white border border-[#e0eaf5] p-3 shadow-sm">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center text-[9px] font-bold text-[#185FA5]">M</div>
            <div>
              <p className="text-xs font-semibold text-[#042C53]">ComCare Short-to-Medium-Term</p>
              <p className="text-[10px] text-[#B4B2A9]">Ministry of Social and Family Development</p>
            </div>
          </div>
          <p className="mt-1.5 text-[10px] text-[#5F5E5A] leading-relaxed">Financial assistance for lower-income families facing difficulties...</p>
          <div className="mt-2 flex gap-1.5">
            <span className="rounded-full bg-[#FAEEDA] border border-[#FAC775] px-2 py-0.5 text-[9px] font-medium text-[#BA7517]">Financial Aid</span>
            <span className="rounded-full bg-[#E6F1FB] border border-[#B5D4F4] px-2 py-0.5 text-[9px] font-medium text-[#185FA5]">Families</span>
            <span className="rounded-full bg-[#F1EFE8] border border-[#D3D1C7] px-2 py-0.5 text-[9px] font-medium text-[#5F5E5A]">Monthly</span>
          </div>
        </div>
        <div className="rounded-xl bg-white/60 border border-[#eef2f7] p-3">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-lg bg-[#e0eaf5]" />
            <div className="h-2.5 w-28 rounded bg-[#e0eaf5]" />
          </div>
          <div className="mt-2 h-2 w-full rounded bg-[#f0f6ff]" />
          <div className="mt-1 h-2 w-3/4 rounded bg-[#f0f6ff]" />
        </div>
      </div>
    </div>
  )
}

function DatabaseIllustration() {
  const shouldReduceMotion = useReducedMotion()
  const cards = [
    { posStyle: { top: "0%", left: "10%", rotate: "-6deg" }, text: "Healthcare", textStyle: "bg-[#E6F1FB] text-[#185FA5]" },
    { posStyle: { top: "0%", left: "50%", rotate: "4deg" }, text: "Education", textStyle: "bg-[#FAEEDA] text-[#BA7517]" },
    { posStyle: { top: "34%", left: "2%", rotate: "2deg" }, text: "Financial Aid", textStyle: "bg-[#fef2f2] text-red-600" },
    { posStyle: { top: "36%", left: "56%", rotate: "-3deg" }, text: "Disability", textStyle: "bg-[#EEEDFE] text-[#534AB7]" },
    { posStyle: { top: "70%", left: "50%", rotate: "5deg" }, text: "Childcare", textStyle: "bg-[#fce7f3] text-rose-600" },
    { posStyle: { top: "70%", left: "10%", rotate: "-2deg" }, text: "Eldercare", textStyle: "bg-[#E6F1FB] text-[#0C447C]" },
  ]

  if (shouldReduceMotion) {
    return (
      <div className="relative flex items-center justify-center py-4">
        <div className="relative h-40 w-full">
          {cards.map(card => (
            <div key={card.text} className="absolute rounded-xl bg-white border border-[#e0eaf5] px-3 py-2 shadow-sm" style={{ ...card.posStyle }}>
              <div className="flex items-center gap-1.5">
                <div className={cn("w-5 h-5 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center text-[8px] sm:text-[12px] font-bold", card.textStyle)}>
                  {card.text.charAt(0)}
                </div>
                <span className="text-[10px] sm:text-[14px] font-medium text-[#444441]">{card.text}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Gravity gravity={{ x: 0, y: 1 }} className="w-full h-full relative">
      {cards.map(card => (
        <MatterBody matterBodyOptions={{ friction: 0.5, restitution: 0.2 }} x={card.posStyle.left} y={card.posStyle.top} key={card.text}>
          <div className="rounded-xl bg-white border border-[#e0eaf5] px-3 py-2 shadow-sm">
            <div className="flex items-center gap-1.5">
              <div className={cn("w-5 h-5 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center text-[8px] sm:text-[12px] font-bold", card.textStyle)}>
                {card.text.charAt(0)}
              </div>
              <span className="text-[10px] sm:text-[14px] font-medium text-[#444441]">{card.text}</span>
            </div>
          </div>
        </MatterBody>
      ))}
    </Gravity>
  )
}

function FilterIllustration() {
  return (
    <div className="rounded-xl bg-[#f7fafd] border border-[#e4edf7] p-4 space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          {["/logos/hdb.jpg", "/logos/MOH.jpg", "/logos/cpf.jpg", "/logos/msf.jpg"].map((src, i) => (
            <img key={i} src={src} alt="" className="h-8 w-8 rounded-full ring-2 ring-white shadow-sm" style={{ marginLeft: i > 0 ? "-8px" : 0 }} />
          ))}
        </div>
        <div className="relative">
          <div className="flex items-center gap-1.5 rounded-full border border-[#e0eaf5] bg-white px-3 py-1.5 shadow-sm">
            <SlidersHorizontal className="h-3.5 w-3.5 text-[#185FA5]" />
            <span className="text-xs font-medium text-[#185FA5]">Filter</span>
          </div>
          <svg className="absolute -bottom-2 -right-1 h-4 w-4 text-[#444441] drop-shadow-sm" viewBox="0 0 16 16" fill="currentColor">
            <path d="M1 1l5.5 14 2.2-5.8L14.5 7z" />
          </svg>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-2 rounded-full border border-[#B5D4F4] bg-[#E6F1FB] px-3 py-1.5 shadow-sm">
          <img src="/logos/sgenable.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-[#185FA5]">Disability Support</span>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-[#e0eaf5] bg-white px-3 py-1.5 shadow-sm">
          <img src="/logos/aic.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-[#5F5E5A]">Eldercare</span>
        </div>
      </div>
      <div className="flex items-center gap-4 text-xs text-[#B4B2A9]">
        <span>Singapore</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-[#EF9F27]" />
          Eligible
        </span>
        <Sparkles className="h-3.5 w-3.5 text-[#D3D1C7]" />
      </div>
    </div>
  )
}

function SuggestSchemeIllustration() {
  return (
    <div className="relative rounded-xl bg-[#f7fafd] border border-[#e4edf7] p-3.5 overflow-hidden">
      <div className="flex items-center gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-[#e0eaf5] text-[#5F5E5A] text-[10px] font-bold">1</div>
        <div className="flex-1 rounded-xl bg-white border border-[#e0eaf5] px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <Globe className="h-3 w-3 shrink-0 text-[#B4B2A9]" />
            <span className="text-[10px] text-[#5F5E5A] truncate">https://gov.sg/schemes/new-grant</span>
          </div>
        </div>
      </div>
      <div className="ml-3 border-l-2 border-dashed border-[#e0eaf5] h-3" />
      <div className="flex items-center gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-[#E6F1FB] text-[#185FA5] text-[10px] font-bold">2</div>
        <div className="flex-1 rounded-xl bg-white border border-[#e0eaf5] px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3 w-3 shrink-0 text-[#185FA5]" />
            <span className="text-[10px] text-[#042C53] font-medium">AI extracting scheme details</span>
          </div>
          <div className="mt-1.5 flex gap-1">
            {["Eligibility", "Benefits", "Agency"].map(t => (
              <span key={t} className="rounded bg-[#E6F1FB] px-1.5 py-0.5 text-[8px] text-[#185FA5]">{t}</span>
            ))}
          </div>
        </div>
      </div>
      <div className="ml-3 border-l-2 border-dashed border-[#e0eaf5] h-3" />
      <div className="flex items-start gap-2.5">
        <div className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-[#042C53] text-white text-[10px] font-bold">3</div>
        <div className="flex-1 rounded-xl bg-white border border-[#e0eaf5] px-2.5 py-2 shadow-sm">
          <div className="flex items-center gap-1.5 mb-1.5">
            <svg className="h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none">
              <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zm1.271 0a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zm0 1.271a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zm6.33 2.521a2.528 2.528 0 0 1 2.52-2.521A2.528 2.528 0 0 1 20.206 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.52V8.834zm-1.272 0a2.528 2.528 0 0 1-2.52 2.521 2.527 2.527 0 0 1-2.521-2.521V2.522A2.527 2.527 0 0 1 11.372 0a2.528 2.528 0 0 1 2.52 2.522v6.312zm-2.52 6.33a2.528 2.528 0 0 1 2.52 2.52 2.527 2.527 0 0 1-2.52 2.522 2.527 2.527 0 0 1-2.521-2.522v-2.52h2.52zm0-1.272a2.528 2.528 0 0 1-2.521-2.52 2.528 2.528 0 0 1 2.521-2.521h6.312A2.528 2.528 0 0 1 24 11.372a2.528 2.528 0 0 1-2.522 2.52h-6.312z" fill="#E01E5A"/>
            </svg>
            <span className="text-[10px] font-semibold text-[#042C53]">#scheme-reviews</span>
          </div>
          <div className="rounded-lg bg-[#f7fafd] border border-[#e4edf7] px-2 py-1.5">
            <p className="text-[10px] text-[#5F5E5A]"><span className="font-semibold text-[#042C53]">New Housing Grant 2025</span> — HDB</p>
            <div className="mt-1.5 flex gap-1.5">
              <span className="flex items-center gap-1 rounded bg-[#185FA5] px-2 py-0.5 text-[9px] font-semibold text-white">
                <UserCheck className="h-2.5 w-2.5" /> Approve
              </span>
              <span className="rounded bg-white border border-[#e0eaf5] px-2 py-0.5 text-[9px] text-[#5F5E5A]">Reject</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Main section ─────────────────────────────────────────── */

export function FeaturesSection() {
  const { t } = useLanguage()

  return (
    <SectionWrapper id="features" className="bg-white overflow-hidden">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">Features</p>
          <h2 className="font-[var(--font-head)] text-3xl font-bold tracking-tight text-[#042C53] md:text-4xl lg:text-[2.75rem]">
            {t.features.heading}
          </h2>
          <p className="mt-4 text-[#5F5E5A] text-lg max-w-2xl mx-auto leading-relaxed">
            {t.features.subtitle}
          </p>
        </motion.div>
      </div>

      {/* Bento grid */}
      <div className="relative mt-16 mx-auto max-w-5xl grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Glow orbs — brand colours */}
        <div className="pointer-events-none absolute z-0 -top-40 -left-20 h-[600px] w-[600px] rounded-full bg-[#EF9F27]/20 opacity-40 blur-[150px]" />
        <div className="pointer-events-none absolute z-0 top-1/4 -right-10 h-[500px] w-[500px] rounded-full bg-[#185FA5]/15 opacity-30 blur-[130px]" />
        <div className="pointer-events-none absolute z-0 -bottom-20 left-1/3 h-[500px] w-[500px] rounded-full bg-[#EF9F27]/10 opacity-40 blur-[120px]" />

        {/* Left column */}
        <div className="relative z-10 flex flex-col gap-5">
          <motion.div
            className="flex-1 rounded-2xl border border-[#e4edf7] bg-white p-6 hover:shadow-lg hover:shadow-[#185FA5]/10 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5 }}
          >
            <SearchIllustration />
            <h3 className="mt-5 text-lg font-bold tracking-tight text-[#042C53]">{t.features.cards.search.title}</h3>
            <p className="mt-2 text-[#5F5E5A] leading-relaxed text-[15px]">{t.features.cards.search.description}</p>
          </motion.div>

          <motion.div
            className="flex-1 rounded-2xl border border-[#e4edf7] bg-white p-6 hover:shadow-lg hover:shadow-[#185FA5]/10 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <SuggestSchemeIllustration />
            <h3 className="mt-5 text-lg font-bold tracking-tight text-[#042C53]">{t.features.cards.suggest.title}</h3>
            <p className="mt-2 text-[#5F5E5A] leading-relaxed text-[15px]">{t.features.cards.suggest.description}</p>
          </motion.div>
        </div>

        {/* Right column */}
        <div className="relative z-10 flex flex-col gap-5">
          <motion.div
            className="flex-1 rounded-2xl border border-[#e4edf7] bg-white p-6 hover:shadow-lg hover:shadow-[#185FA5]/10 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="w-full h-[200px] sm:h-[300px] relative">
              <DatabaseIllustration />
            </div>
            <h3 className="mt-4 text-lg font-bold tracking-tight text-[#042C53]">{t.features.cards.database.title}</h3>
            <p className="mt-2 text-[#5F5E5A] leading-relaxed text-[15px]">{t.features.cards.database.description}</p>
          </motion.div>

          <motion.div
            className="flex-1 rounded-2xl border border-[#e4edf7] bg-white p-6 hover:shadow-lg hover:shadow-[#185FA5]/10 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.15 }}
          >
            <FilterIllustration />
            <h3 className="mt-4 text-lg font-bold tracking-tight text-[#042C53]">{t.features.cards.filter.title}</h3>
            <p className="mt-2 text-[#5F5E5A] leading-relaxed text-[15px]">{t.features.cards.filter.description}</p>
          </motion.div>
        </div>
      </div>
    </SectionWrapper>
  )
}
