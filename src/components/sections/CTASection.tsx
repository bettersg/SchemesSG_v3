import { motion } from "motion/react"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/i18n"

export function CTASection() {
  const { t } = useLanguage()

  return (
    <section className="relative bg-neutral-950 py-24 px-6 overflow-hidden">
      {/* Decorative gradient orbs */}
      <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 h-[500px] w-[500px] rounded-full bg-amber-400/10 blur-[120px]" />
      <div className="pointer-events-none absolute -bottom-20 right-[10%] h-[300px] w-[300px] rounded-full bg-blue-400/5 blur-[80px]" />

      <motion.div
        className="relative mx-auto max-w-2xl text-center"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="font-serif text-3xl font-bold text-white tracking-tight md:text-4xl lg:text-5xl">
          {t.cta.headline}
        </h2>
        <p className="mt-5 text-neutral-400 text-lg leading-relaxed max-w-xl mx-auto">
          {t.cta.subtitle}
        </p>
        <Button
          size="lg"
          className="mt-9 rounded-full bg-amber-400 text-neutral-900 hover:bg-amber-500 px-10 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200 border-0"
          asChild
        >
          <a href="https://schemes.sg">
            {t.cta.button}
            <ArrowRight className="h-4 w-4" />
          </a>
        </Button>
        <p className="mt-4 text-sm text-neutral-500">{t.cta.note}</p>
      </motion.div>
    </section>
  )
}
