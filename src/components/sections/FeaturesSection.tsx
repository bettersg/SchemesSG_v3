import { motion } from "motion/react"
import { Search, SlidersHorizontal, Sparkles } from "lucide-react"
import { SectionWrapper } from "@/components/shared/SectionWrapper"

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
            <img src="/logos/msf.jpg" alt="" className="h-6 w-6 rounded-full" />
            <div>
              <p className="text-xs font-semibold text-neutral-800">ComCare Short-to-Medium-Term</p>
              <p className="text-[10px] text-neutral-400">Ministry of Social and Family Development</p>
            </div>
          </div>
          <p className="mt-1.5 text-[10px] text-neutral-500 leading-relaxed">Financial assistance for lower-income families facing difficulties...</p>
          <div className="mt-2 flex gap-1.5">
            <span className="rounded-full bg-lime-50 border border-lime-200 px-2 py-0.5 text-[9px] font-medium text-lime-700">Financial Aid</span>
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
  return (
    <div className="relative flex items-center justify-center py-4">
      {/* Scattered scheme category cards */}
      <div className="relative h-40 w-full">
        <div className="absolute top-2 left-4 rotate-[-6deg] rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-blue-100 flex items-center justify-center text-[8px] font-bold text-blue-600">H</div>
            <span className="text-[10px] font-medium text-neutral-700">Healthcare</span>
          </div>
        </div>
        <div className="absolute top-0 right-6 rotate-[4deg] rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-amber-100 flex items-center justify-center text-[8px] font-bold text-amber-600">E</div>
            <span className="text-[10px] font-medium text-neutral-700">Education</span>
          </div>
        </div>
        <div className="absolute top-14 left-12 rotate-[2deg] rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-md">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-lime-100 flex items-center justify-center text-[8px] font-bold text-lime-600">F</div>
            <span className="text-[10px] font-medium text-neutral-700">Financial Aid</span>
          </div>
        </div>
        <div className="absolute top-16 right-4 rotate-[-3deg] rounded-lg bg-white border border-neutral-200 px-3 py-2 shadow-sm">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-rose-100 flex items-center justify-center text-[8px] font-bold text-rose-600">D</div>
            <span className="text-[10px] font-medium text-neutral-700">Disability</span>
          </div>
        </div>
        <div className="absolute bottom-0 left-6 rotate-[5deg] rounded-lg bg-white/70 border border-neutral-100 px-3 py-2">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-purple-100 flex items-center justify-center text-[8px] font-bold text-purple-600">C</div>
            <span className="text-[10px] font-medium text-neutral-500">Childcare</span>
          </div>
        </div>
        <div className="absolute bottom-2 right-10 rotate-[-2deg] rounded-lg bg-white/60 border border-neutral-100 px-3 py-2">
          <div className="flex items-center gap-1.5">
            <div className="h-5 w-5 rounded bg-teal-100 flex items-center justify-center text-[8px] font-bold text-teal-600">E</div>
            <span className="text-[10px] font-medium text-neutral-400">Eldercare</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function FilterIllustration() {
  return (
    <div className="rounded-xl bg-neutral-50 border border-neutral-100 p-4 space-y-4">
      {/* Agency logo row + filter */}
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          <img src="/logos/hdb.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm" />
          <img src="/logos/MOH.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
          <img src="/logos/cpf.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
          <img src="/logos/msf.jpg" alt="" className="h-8 w-8 rounded-full ring-2 ring-neutral-50 shadow-sm -ml-2" />
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
          <img src="/logos/sgenable.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-neutral-700">Disability Support</span>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 shadow-sm">
          <img src="/logos/aic.jpg" alt="" className="h-5 w-5 rounded-full" />
          <span className="text-xs font-medium text-neutral-700">Eldercare</span>
        </div>
      </div>
      {/* Tags row */}
      <div className="flex items-center gap-4 text-xs text-neutral-500">
        <span>Singapore</span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-lime-400" />
          Eligible
        </span>
        <Sparkles className="h-3.5 w-3.5 text-neutral-300" />
      </div>
    </div>
  )
}

function EligibilityIllustration() {
  return (
    <div className="relative rounded-xl bg-neutral-50 border border-neutral-100 p-4 overflow-hidden">
      {/* Mock profile scan UI */}
      <div className="flex flex-col items-center">
        <div className="relative">
          <div className="h-16 w-16 rounded-full bg-neutral-200 flex items-center justify-center text-neutral-400 text-lg font-bold">
            ?
          </div>
          {/* Scan corners */}
          <div className="absolute -top-1 -left-1 h-4 w-4 border-t-2 border-l-2 border-lime-400 rounded-tl" />
          <div className="absolute -top-1 -right-1 h-4 w-4 border-t-2 border-r-2 border-lime-400 rounded-tr" />
          <div className="absolute -bottom-1 -left-1 h-4 w-4 border-b-2 border-l-2 border-lime-400 rounded-bl" />
          <div className="absolute -bottom-1 -right-1 h-4 w-4 border-b-2 border-r-2 border-lime-400 rounded-br" />
        </div>
        {/* Progress bar */}
        <div className="mt-4 w-40 h-2 rounded-full bg-neutral-200 overflow-hidden">
          <div className="h-full w-3/4 rounded-full bg-gradient-to-r from-lime-300 to-lime-400" />
        </div>
      </div>
      {/* Loading text */}
      <div className="mt-4 flex items-center justify-center gap-2">
        <div className="h-4 w-4 rounded-full border-2 border-lime-400 border-t-transparent animate-spin" />
        <span className="text-xs text-neutral-500">Checking eligibility...</span>
      </div>
    </div>
  )
}

function AgencyLogosIllustration() {
  return (
    <div className="flex shrink-0 items-center">
      <img src="/logos/hdb.jpg" alt="" className="h-10 w-10 rounded-full shadow-sm ring-2 ring-white" />
      <img src="/logos/MOH.jpg" alt="" className="h-10 w-10 rounded-full shadow-sm ring-2 ring-white -ml-2" />
      <img src="/logos/cpf.jpg" alt="" className="h-10 w-10 rounded-full shadow-sm ring-2 ring-white -ml-2" />
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main section                                                       */
/* ------------------------------------------------------------------ */

export function FeaturesSection() {
  return (
    <SectionWrapper id="features" className="bg-white">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            Tools That Work Hard as You
          </h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            Explore features that streamline your search and connect you with the right schemes.
          </p>
        </motion.div>
      </div>

      {/* Bento grid — two flex columns */}
      <div className="mt-16 mx-auto max-w-5xl grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Left column */}
        <div className="flex flex-col gap-5">
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
              Find Schemes That Fit You
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              Describe your situation in plain English. Our AI understands your needs and finds the most relevant schemes — no jargon required.
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
            <EligibilityIllustration />
            <h3 className="mt-5 text-lg font-bold tracking-tight">
              Check Your Eligibility
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              Answer a few simple questions and we&rsquo;ll show you which schemes you&rsquo;re likely eligible for, saving you hours of research.
            </p>
          </motion.div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-5">
          {/* Card 2 — Comprehensive Database */}
          <motion.div
            className="flex-1 rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <DatabaseIllustration />
            <h3 className="mt-4 text-lg font-bold tracking-tight">
              500+ Schemes, One Place.
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              Access government and community schemes from agencies like MSF, MOH, HDB, CPF, and more — all in one searchable database.
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
              Find the Right Scheme, No Noise
            </h3>
            <p className="mt-2 text-muted-foreground leading-relaxed text-[15px]">
              Use filters to narrow down schemes by agency, category, eligibility criteria, and the type of support you need.
            </p>
          </motion.div>

          {/* Card 5 — 200+ Agencies */}
          <motion.div
            className="rounded-2xl border border-neutral-200/60 bg-white p-6 hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.5, delay: 0.25 }}
          >
            <div className="flex items-center gap-4">
              <AgencyLogosIllustration />
              <div className="min-w-0">
                <h3 className="text-lg font-bold tracking-tight">
                  200+ Trusted Agencies.
                </h3>
                <p className="mt-1 text-muted-foreground leading-relaxed text-[15px]">
                  Government ministries, statutory boards, and community organisations.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </SectionWrapper>
  )
}
