import { type ReactNode } from "react"
import { motion, useReducedMotion } from "motion/react"
import { cn } from "@/lib/utils"

interface MarqueeProps<T> {
  items: T[]
  renderItem: (item: T, index: number, isHighlighted: boolean) => ReactNode
  renderStaticItem: (item: T, index: number, isHighlighted: boolean) => ReactNode
  highlightIndex?: number
  direction?: "up" | "down"
  speed?: number
  itemHeight: number
  height?: number
  className?: string
  innerClassName?: string
}

export function Marquee<T>({
  items,
  renderItem,
  renderStaticItem,
  highlightIndex = 0,
  direction = "up",
  speed = 25,
  itemHeight,
  height = 420,
  className,
  innerClassName,
}: MarqueeProps<T>) {
  const shouldReduceMotion = useReducedMotion()
  const duplicated = [...items, ...items, ...items]
  const totalHeight = items.length * itemHeight

  if (shouldReduceMotion) {
    return (
      <div className={cn("flex flex-col", className)}>
        {items.map((item, i) =>
          renderStaticItem(item, i, i === highlightIndex)
        )}
      </div>
    )
  }

  return (
    <div
      className={cn("relative overflow-hidden", className)}
      style={{
        height,
        maskImage:
          "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
        WebkitMaskImage:
          "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
      }}
    >
      <motion.div
        className={cn("flex flex-col", innerClassName)}
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
        {duplicated.map((item, index) =>
          renderItem(item, index, index % items.length === highlightIndex)
        )}
      </motion.div>
    </div>
  )
}
