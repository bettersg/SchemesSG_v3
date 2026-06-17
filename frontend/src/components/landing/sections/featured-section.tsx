"use client";

import { motion } from "framer-motion";
import { useLanguage } from "@/lib/landing-i18n";
import { cn } from "@/lib/utils";
import Image from "next/image";
import {
  cssTransition,
  motionPreset,
  transition,
  viewport,
} from "@/lib/design-system/motion";

const featuredLogos = [
  { name: "Channel NewsAsia", src: "/landing/featured/cna-logo.svg" },
  { name: "Lianhe Zaobao", src: "/landing/featured/lianhe-zaobao-logo.svg" },
  { name: "Money FM", src: "/landing/featured/moneyfm-logo.svg" },
  { name: "Better.sg", src: "/landing/featured/bettersg-logo.svg" },
  { name: "Sengkang Town Council", src: "/landing/featured/sengkang-logo.svg" },
  { name: "Hatch", src: "/landing/featured/hatch-logo.png" },
];

const partnerLogos = [
  {
    name: "Singapore Association of Social Workers",
    src: "/landing/featured/sasw.png",
  },
  { name: "Care Corner Singapore", src: "/landing/featured/carecorner.png" },
];

export function FeaturedSection() {
  const { t } = useLanguage();

  return (
    <section className="border-t border-neutral-200/60 bg-neutral-50 py-14 px-6">
      <motion.div
        className="mx-auto max-w-5xl"
        initial={motionPreset.fadeInUpSm.initial}
        whileInView={motionPreset.fadeInUpSm.animate}
        viewport={viewport.close}
        transition={transition.entrance}
      >
        <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
          {t.featured.heading}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-8 md:gap-x-8">
          {featuredLogos.map((logo) => (
            <Image
              key={logo.name}
              src={logo.src}
              alt={logo.name}
              width={160}
              height={64}
              unoptimized
              className={cn(
                "w-auto object-contain",
                cssTransition.opacityState,
                logo.name === "Better.sg" ? "h-10 md:h-11" : "h-14 md:h-16",
              )}
            />
          ))}
        </div>

        <div className="mt-10 pt-10 border-t border-neutral-100">
          <p className="text-center text-sm font-medium uppercase tracking-widest text-neutral-400 mb-10">
            {t.featured.partnersHeading}
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8">
            {partnerLogos.map((logo) => (
              <Image
                key={logo.name}
                src={logo.src}
                alt={logo.name}
                width={180}
                height={64}
                unoptimized
                className={`${cssTransition.opacityState} h-14 md:h-16 w-auto object-contain`}
              />
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
