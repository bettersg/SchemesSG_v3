"use client"

import { cn } from "@/lib/landing-utils"

interface SectionWrapperProps {
  children: React.ReactNode
  className?: string
  id?: string
}

export function SectionWrapper({ children, className, id }: SectionWrapperProps) {
  return (
    <section id={id} className={cn("py-20 px-6 md:py-28", className)}>
      <div className="mx-auto max-w-7xl">{children}</div>
    </section>
  )
}
