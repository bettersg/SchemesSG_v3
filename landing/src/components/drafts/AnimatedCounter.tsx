"use client"

import { useEffect, useRef, useState } from "react"
import { useInView, useReducedMotion } from "framer-motion"

interface AnimatedCounterProps {
  target: number
  suffix?: string
  prefix?: string
  duration?: number
}

export function AnimatedCounter({
  target,
  suffix = "",
  prefix = "",
  duration = 2000,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null)
  const isInView = useInView(ref, { once: true })
  const shouldReduceMotion = useReducedMotion()
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!isInView) return
    if (shouldReduceMotion) {
      setCount(target)
      return
    }

    let start = 0
    const startTime = performance.now()

    function tick(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      start = Math.round(eased * target)
      setCount(start)
      if (progress < 1) {
        rafId = requestAnimationFrame(tick)
      }
    }

    let rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [isInView, target, duration, shouldReduceMotion])

  return (
    <span ref={ref}>
      {prefix}
      {count.toLocaleString()}
      {suffix}
    </span>
  )
}
