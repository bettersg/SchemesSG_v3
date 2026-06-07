"use client";

import { Accordion } from "@heroui/react";
import { ChevronDown } from "lucide-react";
import {
  statusStepContainerClass,
  statusStepIndicatorClass,
  statusStepSummaryClass,
} from "@/components/chat/status-step-styles";
import { StatusStep } from "@/providers/chat-provider";

type StatusStepsAccordionProps = {
  steps: StatusStep[];
};

export function StatusStepsAccordion({ steps }: StatusStepsAccordionProps) {
  if (!steps.length) return null;

  return (
    <Accordion hideSeparator className={`${statusStepContainerClass} p-0`}>
      <Accordion.Item id="response-steps" className="w-full bg-transparent">
        <Accordion.Heading className="w-fit max-w-max">
          <Accordion.Trigger
            className={`${statusStepSummaryClass} cursor-pointer hover:bg-(--schemes-status-info-bg) hover:text-(--schemes-blue-600)`}
          >
            <Accordion.Indicator
              className={`${statusStepIndicatorClass} ms-0! me-0! ml-0! mr-0! grow-0 basis-3.5 text-(--schemes-status-info-text)`}
            >
              <ChevronDown
                size={13}
                strokeWidth={2}
                className="h-3.5 w-3.5 shrink-0"
              />
            </Accordion.Indicator>
            <span className="w-max shrink-0">
              Processed {steps.length} {steps.length === 1 ? "step" : "steps"}
            </span>
          </Accordion.Trigger>
        </Accordion.Heading>
        <Accordion.Panel>
          <Accordion.Body className="py-0">
            <ol className="py-1.5 space-y-2 text-xs font-medium text-(--schemes-ink-soft)">
              {steps.map((step) => (
                <li key={step.id} className="flex items-center gap-2">
                  {step.message}
                </li>
              ))}
            </ol>
          </Accordion.Body>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
