import { motion, useReducedMotion } from "motion/react"
import { MapPin } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Agency } from "@/data/agencies"

interface ScrollingLogoColumnProps {
  agencies: Agency[]
  speed?: number
  className?: string
}

export function ScrollingLogoColumn({
  agencies,
  speed = 30,
  className,
}: ScrollingLogoColumnProps) {
  const shouldReduceMotion = useReducedMotion()
  const duplicated = [...agencies, ...agencies, ...agencies]
  const itemHeight = 56
  const totalHeight = agencies.length * itemHeight

  if (shouldReduceMotion) {
    return (
      <div className={cn("flex flex-col items-end gap-1", className)}>
        {agencies.map((agency, i) => (
          <div
            key={agency.shortName}
            className={cn(
              "flex h-[56px] items-center gap-2.5",
              i === 2 ? "opacity-100" : "opacity-30"
            )}
            title={agency.name}
          >
            <span className="text-sm text-muted-foreground font-medium">
              {agency.shortName}
            </span>
            <img
              src={agency.logo}
              alt={agency.name}
              className="h-9 w-9 rounded-full object-cover bg-white shadow-sm"
              loading="lazy"
            />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div
      className={cn("relative h-[420px] overflow-hidden", className)}
      style={{
        maskImage: "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
        WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
      }}
    >

      <motion.div
        className="flex flex-col items-end"
        animate={{
          y: [-totalHeight, 0],
        }}
        transition={{
          y: {
            duration: speed,
            repeat: Infinity,
            ease: "linear",
          },
        }}
      >
        {duplicated.map((agency, index) => {
          const isHighlighted = index % agencies.length === 2
          return (
            <div
              key={`${agency.shortName}-${index}`}
              className={cn(
                "flex h-[56px] items-center gap-2 transition-opacity duration-300",
                isHighlighted ? "opacity-100" : "opacity-30"
              )}
              title={agency.name}
            >
              {isHighlighted && (
                <MapPin className="h-3.5 w-3.5 shrink-0 text-rose-500" />
              )}
              <span
                className={cn(
                  "text-[14px] whitespace-nowrap",
                  isHighlighted
                    ? "text-foreground font-semibold"
                    : "text-muted-foreground font-medium"
                )}
              >
                {agency.shortName}
              </span>
              <img
                src={agency.logo}
                alt={agency.name}
                className={cn(
                  "h-9 w-9 shrink-0 rounded-full object-cover bg-white transition-all duration-300",
                  isHighlighted
                    ? "shadow-md ring-2 ring-lime-300"
                    : "shadow-sm"
                )}
                loading="lazy"
              />
            </div>
          )
        })}
      </motion.div>
    </div>
  )
}
