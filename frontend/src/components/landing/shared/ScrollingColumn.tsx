"use client"

import { cn } from "@/lib/landing-utils"
import { Marquee } from "./Marquee"

interface ScrollingColumnProps {
  items: string[]
  direction?: "up" | "down"
  highlightIndex?: number
  speed?: number
  className?: string
}

const ITEM_HEIGHT = 52

function Item({ item, isHighlighted }: { item: string; isHighlighted: boolean }) {
  return (
    <div
      className={cn(
        "flex h-[52px] items-center px-3 text-[15px] font-medium whitespace-nowrap transition-opacity duration-300",
        isHighlighted ? "opacity-100" : "opacity-40"
      )}
    >
      {isHighlighted && (
        <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-amber-500" />
      )}
      {item}
    </div>
  )
}

export function ScrollingColumn({
  items,
  direction = "up",
  highlightIndex = 3,
  speed = 25,
  className,
}: ScrollingColumnProps) {
  return (
    <Marquee
      items={items}
      itemHeight={ITEM_HEIGHT}
      direction={direction}
      highlightIndex={highlightIndex}
      speed={speed}
      className={className}
      renderItem={(item, index, isHighlighted) => (
        <Item key={`${item}-${index}`} item={item} isHighlighted={isHighlighted} />
      )}
      renderStaticItem={(item, _i, isHighlighted) => (
        <Item key={item} item={item} isHighlighted={isHighlighted} />
      )}
    />
  )
}
