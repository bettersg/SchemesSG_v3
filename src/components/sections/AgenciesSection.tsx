import { motion } from "motion/react"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { agencies } from "@/data/agencies"
import type { Agency } from "@/data/agencies"

// Split agencies into rows, shuffled for variety
const rows: Agency[][] = [
  agencies.slice(0, 5),
  agencies.slice(5, 10),
  agencies.slice(10, 15),
  agencies.slice(15, 20),
  agencies.slice(20, 24),
]

function MarqueeRow({
  items,
  direction = "left",
  speed = 35,
}: {
  items: Agency[]
  direction?: "left" | "right"
  speed?: number
}) {
  // Triple the items for seamless looping
  const duplicated = [...items, ...items, ...items]

  return (
    <div className="flex overflow-hidden">
      <motion.div
        className="flex shrink-0 gap-4"
        animate={{
          x: direction === "left" ? ["0%", "-33.333%"] : ["-33.333%", "0%"],
        }}
        transition={{
          x: {
            duration: speed,
            repeat: Infinity,
            ease: "linear",
          },
        }}
      >
        {duplicated.map((agency, index) => (
          <div
            key={`${agency.shortName}-${index}`}
            className="flex shrink-0 items-center gap-3 rounded-full border border-neutral-200/60 bg-white/80 px-4 py-2.5 shadow-sm"
          >
            <img
              src={agency.logo}
              alt={agency.name}
              className="h-9 w-9 rounded-full object-cover bg-neutral-100"
              loading="lazy"
            />
            <span className="text-[15px] font-medium text-neutral-700 whitespace-nowrap">
              {agency.shortName}
            </span>
          </div>
        ))}
      </motion.div>
    </div>
  )
}

export function AgenciesSection() {
  return (
    <section id="about" className="relative bg-neutral-50/80 py-20 overflow-hidden">
      {/* Header content */}
      <div className="relative z-10 mx-auto max-w-7xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            Discover Schemes From{"\n"}
            <br className="hidden sm:inline" />
            200+ Agencies
          </h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            We index schemes from Singapore&rsquo;s key government ministries, statutory boards, and community organisations.
          </p>
          <Button
            size="lg"
            className="mt-7 rounded-full bg-neutral-900 hover:bg-neutral-800 text-white px-8 py-6 text-base font-semibold gap-2 shadow-none cursor-pointer transition-all duration-200"
            asChild
          >
            <a href="https://schemes.sg">
              Get Started <ArrowRight className="h-4 w-4" />
            </a>
          </Button>
        </motion.div>
      </div>

      {/* Scrolling marquee rows */}
      <div className="relative mt-14">
        {/* Left/right gradient masks */}
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-40 bg-gradient-to-r from-neutral-50/80 to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-40 bg-gradient-to-l from-neutral-50/80 to-transparent" />
        {/* Top/bottom gradient masks for fading outer rows */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-16 bg-gradient-to-b from-neutral-50/80 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-16 bg-gradient-to-t from-neutral-50/80 to-transparent" />

        <div className="flex flex-col gap-4">
          {rows.map((row, i) => (
            <MarqueeRow
              key={i}
              items={row}
              direction={i % 2 === 0 ? "left" : "right"}
              speed={30 + i * 5}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
