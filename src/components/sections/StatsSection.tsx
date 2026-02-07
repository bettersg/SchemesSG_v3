import { motion } from "motion/react"
import { AnimatedCounter } from "@/components/shared/AnimatedCounter"
import { useLanguage } from "@/i18n"

const statValues = [
  { value: 500, suffix: "+" },
  { value: 200, suffix: "+" },
]

export function StatsSection() {
  const { t } = useLanguage()

  return (
    <section className="bg-neutral-900 py-16 px-6">
      <div className="mx-auto max-w-5xl">
        <motion.div
          className="grid grid-cols-2 gap-8 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5 }}
        >
          {t.stats.items.map((stat, index) => (
            <div key={index}>
              <div className="text-4xl font-bold text-white md:text-5xl lg:text-6xl tracking-tight">
                <AnimatedCounter
                  target={statValues[index].value}
                  suffix={statValues[index].suffix}
                  duration={2000}
                />
              </div>
              <p className="mt-2 text-sm font-medium uppercase tracking-wider text-amber-400/70">
                {stat.label}
              </p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
