"use client"

import { useEffect, useMemo, useRef, useState, type Dispatch, type ReactNode, type RefObject, type SetStateAction } from "react"
import { motion, useInView, useReducedMotion } from "framer-motion"
import { cn } from "@/lib/landing-utils"

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
  const duplicated = useMemo(() => [...items, ...items, ...items], [items])
  const totalHeight = items.length * itemHeight
  const [highlightIdx, setHighlightIdx] = useState(highlightIndex)
  const container = useRef<HTMLDivElement>(null)

  if (shouldReduceMotion) {
    return (
      <div className={cn("flex flex-col", className)}>
        {items.map((item, i) =>
          <div key={i} className="cursor-default" onMouseOver={() => setHighlightIdx(i)}>{renderStaticItem(item, i, i === highlightIdx)}</div>
        )}
      </div>
    )
  }

  return (
    <div
      className={cn("relative overflow-hidden flex items-center-safe", className)}
      style={{
        height,
        maskImage:
          "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
        WebkitMaskImage:
          "linear-gradient(to bottom, transparent 0%, black 25%, black 75%, transparent 100%)",
      }}
    >
	<div className={cn("flex items-center")} style={{ height: itemHeight }} ref={container}>

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
			  {
				return <MarqueeAnimatedItem key={index} item={item} index={index} renderItem={renderItem} containerRef={container} itemHeight={itemHeight} highlightIdx={highlightIdx} setHighlightIdx={setHighlightIdx}/>}
			)}
      </motion.div>
		</div>
    </div>
  )
}

interface MarqueeAnimatedItemProps<T> {
	item: T
	index: number
	renderItem: (item: T, index: number, isHighlighted: boolean) => ReactNode
	containerRef: RefObject<HTMLDivElement | null>
	itemHeight: number
	highlightIdx: number
	setHighlightIdx: Dispatch<SetStateAction<number>>
}

function MarqueeAnimatedItem<T>({item, index, renderItem, containerRef, itemHeight, highlightIdx, setHighlightIdx} : MarqueeAnimatedItemProps<T>) {
	const ref = useRef(null)
	const isInCenter = useInView(ref, {root: containerRef, margin: `${itemHeight}px 0px 0px 0px`})
	useEffect(() => {
		if (isInCenter) {
			setHighlightIdx(index)
		}
	}, [isInCenter, index, setHighlightIdx])

	return <div className="cursor-default" ref={ref}>{renderItem(item, index, index === highlightIdx)}</div>
}