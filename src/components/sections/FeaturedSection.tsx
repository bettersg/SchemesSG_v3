import { motion } from "motion/react"

const featuredLogos = [
  { name: "Channel NewsAsia", src: "/featured/cna-logo.fe6e55ec.svg" },
  { name: "Lianhe Zaobao", src: "/featured/lianhe-zaobao-logo.c41c922e.svg" },
  { name: "Money FM", src: "/featured/moneyfm-logo.c4778b09.svg" },
  { name: "Better.sg", src: "/featured/bettersg-logo.a549b628.svg" },
  { name: "Sengkang Town Council", src: "/featured/sengkang-logo.4fef7e5f.svg" },
  { name: "Hatch", src: "/featured/hatch-logo.5129b052.svg" },
]

const partnerLogos = [
  { name: "Singapore Association of Social Workers", src: "/featured/sasw.a489ae5f.png" },
  { name: "Care Corner Singapore", src: "/featured/carecorner.cf5eba1a.png" },
]

export function FeaturedSection() {
  return (
    <section className="border-t border-neutral-200/60 bg-white py-14 px-6">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={{ opacity: 0, y: 10 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-40px" }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
          Featured on
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8 md:gap-x-16">
          {featuredLogos.map((logo) => (
            <img
              key={logo.name}
              src={logo.src}
              alt={logo.name}
              className="h-10 md:h-12 w-auto object-contain brightness-0 opacity-40 hover:opacity-70 transition-opacity duration-200"
            />
          ))}
        </div>

        <div className="mt-10 pt-10 border-t border-neutral-100">
          <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
            Our Partners
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-14 gap-y-8">
            {partnerLogos.map((logo) => (
              <img
                key={logo.name}
                src={logo.src}
                alt={logo.name}
                className="h-12 md:h-14 w-auto object-contain opacity-60 hover:opacity-90 transition-opacity duration-200"
              />
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  )
}
