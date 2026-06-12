"use client"

import { motion } from "framer-motion"
import { Accordion } from "@heroui/react"
import { Button } from "@/components/landing/ui/button"
import { SectionWrapper } from "@/components/landing/shared/section-wrapper"
import { useLanguage } from "@/lib/landing-i18n"
import { ChevronDown, MessageCircle } from "lucide-react"

export function FAQSection() {
  const { t } = useLanguage()

  return (
    <SectionWrapper id="faq" className="bg-neutral-50/60">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            {t.faq.heading}
          </h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed">
            {t.faq.subtitle}
          </p>
        </motion.div>
      </div>

      <div className="mt-14 mx-auto max-w-5xl grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        {/* Left column — Accordion */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Accordion className="flex flex-col gap-3">
            {t.faq.items.map((item, index) => (
              <Accordion.Item
                key={index}
                className="rounded-xl border border-neutral-200/80 bg-white shadow-sm"
              >
                <Accordion.Heading>
					<Accordion.Trigger className="text-left font-semibold text-[15px] hover:no-underline cursor-pointer py-5">
					  {item.question}
					  <Accordion.Indicator><ChevronDown/></Accordion.Indicator>
					</Accordion.Trigger>
				</Accordion.Heading>
                <Accordion.Panel>
					<Accordion.Body className="text-muted-foreground leading-relaxed text-[15px] pb-5">
					  {item.answer}
					</Accordion.Body>
				</Accordion.Panel>
              </Accordion.Item>
            ))}
          </Accordion>
        </motion.div>

        {/* Right column — Support card */}
        <motion.div
          id="contribute"
          className="flex"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="flex-1 flex flex-col rounded-2xl border border-neutral-200/80 bg-white p-8 shadow-sm">
            {/* Illustration */}
            <div className="flex items-start gap-2 mb-6">
              <div className="h-14 w-20 rounded-lg bg-neutral-100 flex items-end justify-center pb-1">
                <div className="h-8 w-14 rounded-md bg-neutral-200/80" />
              </div>
              <div className="h-8 w-8 rounded-lg bg-amber-400 flex items-center justify-center -ml-3 mt-4 shadow-sm">
                <MessageCircle className="h-4 w-4 text-neutral-900" strokeWidth={2} />
              </div>
            </div>

            <h3 className="text-lg font-bold tracking-tight">
              {t.faq.sidebar.title}
            </h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {t.faq.sidebar.description}
            </p>

            <div className="mt-auto pt-6" />

            <Button
              className="rounded-full bg-neutral-900 hover:bg-neutral-800 text-white px-6 py-5 text-sm font-semibold cursor-pointer shadow-none"
            >
              <a href="/contribute" target="_blank" rel="noopener noreferrer">
                {t.faq.sidebar.cta}
              </a>
            </Button>
          </div>
        </motion.div>
      </div>
    </SectionWrapper>
  )
}
