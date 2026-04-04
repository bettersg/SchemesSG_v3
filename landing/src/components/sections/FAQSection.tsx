"use client"

import { motion } from "framer-motion"
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion"
import { MessageCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SectionWrapper } from "@/components/shared/SectionWrapper"
import { useLanguage } from "@/lib/landing-i18n"

export function FAQSection() {
  const { t } = useLanguage()

  return (
    <SectionWrapper id="faq" className="bg-white">
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
        >
          <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">FAQ</p>
          <h2 className="font-[var(--font-head)] text-3xl font-bold tracking-tight text-[#042C53] md:text-4xl lg:text-[2.75rem]">
            {t.faq.heading}
          </h2>
          <p className="mt-4 text-[#5F5E5A] text-lg max-w-2xl mx-auto leading-relaxed">
            {t.faq.subtitle}
          </p>
        </motion.div>
      </div>

      <div className="mt-14 mx-auto max-w-5xl grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        {/* Accordion */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Accordion type="single" collapsible className="flex flex-col gap-3">
            {t.faq.items.map((item, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="rounded-xl border border-[#e4edf7] bg-white px-6 shadow-sm data-[state=open]:shadow-md data-[state=open]:border-[#B5D4F4] transition-all duration-200"
              >
                <AccordionTrigger className="text-left font-semibold text-[15px] text-[#042C53] hover:no-underline cursor-pointer py-5">
                  {item.question}
                </AccordionTrigger>
                <AccordionContent className="text-[#5F5E5A] leading-relaxed text-[15px] pb-5">
                  {item.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>

        {/* Sidebar card */}
        <motion.div
          id="contribute"
          className="flex"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="flex-1 flex flex-col items-center md:items-start rounded-2xl border border-[#e4edf7] bg-[#f7fafd] p-8 shadow-sm">
            <div className="flex items-start gap-2 mb-6">
              <div className="h-14 w-20 rounded-xl bg-[#E6F1FB] border border-[#B5D4F4] flex items-end justify-center pb-1">
                <div className="h-8 w-14 rounded-lg bg-[#B5D4F4]" />
              </div>
              <div className="h-8 w-8 rounded-xl bg-[#EF9F27] flex items-center justify-center -ml-3 mt-4 shadow-sm">
                <MessageCircle className="h-4 w-4 text-white" strokeWidth={2} />
              </div>
            </div>
            <h3 className="text-lg font-bold tracking-tight text-[#042C53]">
              {t.faq.sidebar.title}
            </h3>
            <p className="mt-2 text-sm text-[#5F5E5A] leading-relaxed text-center md:text-left">
              {t.faq.sidebar.description}
            </p>
            <div className="mt-auto pt-6" />
            <Button
              className="rounded-full bg-[#042C53] hover:bg-[#0C447C] text-white px-6 py-5 text-sm font-semibold cursor-pointer shadow-none border-0"
              asChild
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
