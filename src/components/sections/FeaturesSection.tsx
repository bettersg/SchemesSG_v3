import { motion } from "motion/react"
import { Search, UserCheck, Database } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { features } from "@/data/content"

const iconMap = {
  search: Search,
  userCheck: UserCheck,
  database: Database,
} as const

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

      <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-3 md:gap-8">
        {features.map((feature, index) => {
          const Icon = iconMap[feature.icon]
          return (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="h-full border-neutral-200/60 bg-card hover:shadow-lg hover:shadow-neutral-200/50 transition-all duration-300 cursor-pointer group">
                <CardContent className="p-8">
                  <div className="inline-flex items-center justify-center rounded-xl bg-neutral-100 p-3 text-neutral-600 group-hover:bg-lime-50 group-hover:text-lime-700 transition-colors duration-200">
                    <Icon className="h-6 w-6" strokeWidth={1.5} />
                  </div>
                  <h3 className="mt-5 text-lg font-semibold tracking-tight">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-muted-foreground leading-relaxed text-[15px]">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>
    </SectionWrapper>
  )
}
