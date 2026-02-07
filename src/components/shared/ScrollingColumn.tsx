import { motion, useReducedMotion } from "motion/react"
import { cn } from "@/lib/utils"

interface ScrollingColumnProps {
  items: string[]
  direction?: "up" | "down"
  highlightIndex?: number
  speed?: number
  className?: string
}

export function ScrollingColumn({
  items,
  direction = "up",
  highlightIndex = 3,
  speed = 25,
  className,
}: ScrollingColumnProps) {
  const shouldReduceMotion = useReducedMotion()
  const duplicated = [...items, ...items, ...items]
  const itemHeight = 52
  const totalHeight = items.length * itemHeight

  if (shouldReduceMotion) {
    return (
      <div className={cn("flex flex-col items-start gap-1", className)}>
        {items.map((item, i) => (
          <div
            key={item}
            className={cn(
              "flex h-[52px] items-center px-3 text-[15px] font-medium whitespace-nowrap",
              i === highlightIndex
                ? "text-foreground font-semibold"
                : "text-muted-foreground/35"
            )}
          >
            {i === highlightIndex && (
              <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-lime-500" />
            )}
            {item}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className={cn("relative h-[420px] overflow-hidden", className)}>
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-28 bg-gradient-to-b from-neutral-50 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-28 bg-gradient-to-t from-neutral-50 to-transparent" />

      <motion.div
        className="flex flex-col"
        animate={{
          y: direction === "up" ? [0, -totalHeight] : [-totalHeight, 0],
        }}
        transition={{
          y: {
            duration: speed,
            repeat: Infinity,
            ease: "linear",
          },
        }}
      >
        {duplicated.map((item, index) => {
          const isHighlighted = index % items.length === highlightIndex
          return (
            <div
              key={`${item}-${index}`}
              className={cn(
                "flex h-[52px] items-center px-3 text-[15px] font-medium whitespace-nowrap transition-colors duration-300",
                isHighlighted
                  ? "text-foreground font-semibold"
                  : "text-muted-foreground/30"
              )}
            >
              {isHighlighted && (
                <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-lime-500" />
              )}
              {item}
            </div>
          )
        })}
      </motion.div>
    </div>
  )
}
