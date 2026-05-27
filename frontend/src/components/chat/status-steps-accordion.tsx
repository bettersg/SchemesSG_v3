"use client";

import { Accordion } from "@heroui/react";
import type { BotStatusStep } from "@/providers";
import { ChevronDown } from "lucide-react";

type StatusStepsAccordionProps = {
  steps: BotStatusStep[];
};

export function StatusStepsAccordion({ steps }: StatusStepsAccordionProps) {
  if (!steps.length) return null;

  return (
    <Accordion
      hideSeparator
      className="block w-full bg-transparent p-0 text-(--schemes-status-info-text)"
    >
      <Accordion.Item id="response-steps" className="w-full bg-transparent">
        <Accordion.Heading className="w-fit max-w-max">
          <Accordion.Trigger className="!inline-flex !w-fit !max-w-max cursor-pointer !justify-start gap-2 rounded-lg !hover:bg-neutral-100 px-3 py-1.5 text-left text-xs font-semibold text-(--schemes-status-info-text) hover:text-(--schemes-blue-600)">
            <Accordion.Indicator className="!ms-0 !me-0 !ml-0 !mr-0 flex h-3.5 w-3.5 shrink-0 grow-0 basis-3.5 items-center justify-center text-(--schemes-status-info-text) [margin-inline-start:0]">
              <ChevronDown
                size={13}
                strokeWidth={2}
                className="h-3.5 w-3.5 shrink-0"
              />
            </Accordion.Indicator>
            <span className="shrink-0 w-max">
              Processed {steps.length} {steps.length === 1 ? "step" : "steps"}
            </span>
          </Accordion.Trigger>
        </Accordion.Heading>
        <Accordion.Panel>
          <Accordion.Body>
            <ol className="py-1.5 space-y-2 text-xs font-medium text-(--schemes-status-info-text)">
              {steps.map((step) => (
                <li key={step.id} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-(--schemes-blue-400)" />
                  <span>{step.label}</span>
                </li>
              ))}
            </ol>
          </Accordion.Body>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
