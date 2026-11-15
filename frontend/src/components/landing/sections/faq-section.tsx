"use client";

import { motion } from "framer-motion";
import { Accordion } from "@heroui/react";
import { Button } from "@/components/landing/ui/button";
import { SectionWrapper } from "@/components/landing/shared/section-wrapper";
import { msg } from "@lingui/core/macro";
import { useLingui } from "@lingui/react";
import { Trans } from "@lingui/react/macro";
import { useSchemeCount } from "@/lib/scheme-count";
import { track } from "@/lib/analytics";
import { ChevronDown, MessageCircle } from "lucide-react";
import {
  delay,
  motionPreset,
  transition,
  viewport,
} from "@/lib/design-system/motion";

const FAQ_ITEMS = [
  {
    question: msg({ message: "What is Schemes.sg?" }),
    answer: msg({
      message:
        "Schemes.sg is a free, AI-powered search tool that helps you find social assistance schemes you may qualify for. It brings together schemes from over 200 government agencies and community organisations.",
    }),
  },
  {
    question: msg({ message: "Is Schemes.sg free to use?" }),
    answer: msg({
      message:
        "Yes. Schemes.sg is free and needs no sign-up. We want everyone to be able to find the help that’s available.",
    }),
  },
  {
    question: msg({ message: "How does the AI matching work?" }),
    answer: msg({
      message:
        "You describe your situation, and we search {schemeCount}+ schemes for the closest matches, using who qualifies, where you live, and more. You can then ask follow-up questions to narrow the results.",
    }),
  },
  {
    question: msg({ message: "What types of schemes are covered?" }),
    answer: msg({
      message:
        "We cover 10 areas: financial assistance, family and children, health and wellbeing, housing and food, education, employment and training, seniors and caregiving, disability and transport, legal and safety, and community support.",
    }),
  },
  {
    question: msg({ message: "Is my personal information safe?" }),
    answer: msg({
      message:
        "Your privacy is protected by design. We don't require any login or account and we never ask for your name or NRIC, which means there's no way for us to know who you are. Your searches are encrypted in transit, we don't sell your information, and the measurements we use to improve the site never include what you typed.",
    }),
    answerLink: {
      label: msg({ message: "Read our Privacy Policy" }),
      href: "/privacy",
    },
  },
  {
    question: msg({ message: "How up-to-date is the information?" }),
    answer: msg({
      message:
        "We update scheme details regularly. Always check the latest with the agency before you apply.",
    }),
  },
  {
    question: msg({ message: "Can I access Schemes.sg data through an API?" }),
    answer: msg({
      message:
        "We share scheme data programmatically with a small number of partner organisations, on request. It is not a self-serve public API. Get in touch if your organisation wants to integrate.",
    }),
    answerLink: {
      label: msg({ message: "Read the developer docs" }),
      href: "/developers",
    },
  },
];

export function FAQSection() {
  const { i18n } = useLingui();
  const schemeCount = useSchemeCount();
  return (
    <SectionWrapper id="faq" className="bg-neutral-50/60">
      <div className="text-center">
        <motion.div
          initial={motionPreset.fadeInUpMd.initial}
          whileInView={motionPreset.fadeInUpMd.animate}
          viewport={viewport.default}
          transition={transition.entrance}
        >
          <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
            <Trans>Common questions</Trans>
          </h2>
        </motion.div>
      </div>

      <div className="mt-14 mx-auto max-w-5xl grid grid-cols-1 gap-8 lg:grid-cols-[1fr_320px]">
        {/* Left column — Accordion */}
        <motion.div
          initial={motionPreset.fadeInUpMd.initial}
          whileInView={motionPreset.fadeInUpMd.animate}
          viewport={viewport.relaxed}
          transition={{ ...transition.entrance, delay: delay.landingSection }}
        >
          <Accordion className="flex flex-col gap-3">
            {FAQ_ITEMS.map((item, index) => (
              <Accordion.Item
                key={index}
                className="rounded-xl border border-neutral-200/80 bg-white shadow-sm"
              >
                <Accordion.Heading>
                  <Accordion.Trigger className="text-left font-semibold text-[15px] hover:no-underline cursor-pointer py-5">
                    {i18n._(item.question)}
                    <Accordion.Indicator>
                      <ChevronDown />
                    </Accordion.Indicator>
                  </Accordion.Trigger>
                </Accordion.Heading>
                <Accordion.Panel>
                  <Accordion.Body className="text-muted-foreground leading-relaxed text-[15px] pb-5">
                    {i18n._({ ...item.answer, values: { schemeCount } })}
                    {item.answerLink && (
                      <a
                        href={item.answerLink.href}
                        onClick={() =>
                          track("select_content", {
                            content_type: "faq_link",
                            // The destination, not the label: it is stable
                            // across languages and copy edits.
                            item_id: item.answerLink!.href,
                          })
                        }
                        className="ml-1 font-medium text-primary underline-offset-4 hover:underline"
                      >
                        {i18n._(item.answerLink.label)}
                      </a>
                    )}
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
          initial={motionPreset.fadeInUpMd.initial}
          whileInView={motionPreset.fadeInUpMd.animate}
          viewport={viewport.relaxed}
          transition={{
            ...transition.entrance,
            delay: delay.landingSectionTrailing,
          }}
        >
          <div className="flex-1 flex flex-col min-w-0 break-words rounded-2xl border border-neutral-200/80 bg-white p-6 sm:p-8 shadow-sm">
            {/* Illustration */}
            <div className="flex items-start gap-2 mb-6">
              <div className="h-14 w-20 rounded-lg bg-neutral-100 flex items-end justify-center pb-1">
                <div className="h-8 w-14 rounded-md bg-neutral-200/80" />
              </div>
              <div className="h-8 w-8 rounded-lg bg-amber-400 flex items-center justify-center -ml-3 mt-4 shadow-sm">
                <MessageCircle
                  className="h-4 w-4 text-neutral-900"
                  strokeWidth={2}
                />
              </div>
            </div>

            <h3 className="text-lg font-bold tracking-tight">
              <Trans>Suggest a new scheme</Trans>
            </h3>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              <Trans>
                Know a scheme we’re missing? Suggest it and help others find
                it.
              </Trans>
            </p>

            <div className="mt-auto pt-6" />

            <Button className="h-auto max-w-full whitespace-normal rounded-full bg-neutral-900 py-5 px-6 text-center text-sm font-semibold text-white shadow-none hover:bg-neutral-800 cursor-pointer">
              <a href="/contribute" target="_blank" rel="noopener noreferrer">
                <Trans comment="Button: go to the contribute page">
                  Suggest a scheme
                </Trans>
              </a>
            </Button>
          </div>
        </motion.div>
      </div>
    </SectionWrapper>
  );
}
