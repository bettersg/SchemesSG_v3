import { motion } from "motion/react"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { testimonial } from "@/data/content"

export function TestimonialSection() {
  return (
    <SectionWrapper className="bg-white">
      <motion.div
        className="mx-auto max-w-3xl text-center"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6 }}
      >
        {/* Avatar on top */}
        <div className="mx-auto h-16 w-16 rounded-full bg-gradient-to-br from-lime-300 to-lime-500 flex items-center justify-center text-neutral-900 font-bold text-xl shadow-lg shadow-lime-300/20 ring-4 ring-white">
          {testimonial.author.charAt(0)}
        </div>

        {/* Name and role */}
        <p className="mt-4 text-sm text-muted-foreground">
          {testimonial.author} &bull; <span className="font-semibold text-foreground">{testimonial.role}</span>
        </p>

        {/* Large serif quote below */}
        <blockquote className="mt-8 font-serif text-2xl leading-relaxed tracking-tight text-foreground md:text-[1.75rem] lg:text-[2rem]">
          &ldquo;{testimonial.quote}&rdquo;
        </blockquote>
      </motion.div>
    </SectionWrapper>
  )
}
