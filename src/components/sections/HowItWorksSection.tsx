import { motion } from "motion/react"
import { Badge } from "@/components/ui/badge"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { howItWorks } from "@/data/content"

export function HowItWorksSection() {
  return (
    <SectionWrapper id="about" className="bg-neutral-50/60">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <Badge
            variant="secondary"
            className="mb-4 rounded-full px-4 py-1 text-xs font-medium bg-lime-50 text-lime-800 border-lime-200"
          >
            How It Works
          </Badge>
          <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            Find Your Schemes in 3 Steps
          </h2>
        </motion.div>
      </div>

      <div className="relative mt-16 mx-auto max-w-5xl">
        {/* Connecting dashed line (desktop) */}
        <div className="absolute top-7 left-[calc(16.67%+24px)] right-[calc(16.67%+24px)] hidden md:block">
          <div className="h-px border-t-2 border-dashed border-neutral-300" />
        </div>

        <div className="grid grid-cols-1 gap-12 md:grid-cols-3 md:gap-8">
          {howItWorks.map((step, index) => (
            <motion.div
              key={step.step}
              className="flex flex-col items-center text-center"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
            >
              <div className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-900 text-white text-lg font-bold shadow-lg shadow-neutral-900/20">
                {step.step}
              </div>
              <h3 className="mt-6 text-lg font-semibold tracking-tight">
                {step.title}
              </h3>
              <p className="mt-3 text-muted-foreground leading-relaxed text-[15px] max-w-[280px]">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </SectionWrapper>
  )
}
