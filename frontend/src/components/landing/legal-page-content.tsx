"use client";

import Link from "next/link";
import { Body, Display, Headline } from "@/components/ui/typography";
import { useLanguage } from "@/lib/landing-i18n";
import {
  productButtonDefault,
  productButtonOutlineBlue,
} from "@/lib/design-system/product-styles";
import { cn } from "@/lib/utils";

const PROSE = "max-w-[68ch]";

/**
 * Privacy and terms.
 *
 * Both pages carry a drafting notice instead of policy text, on purpose: the
 * routes exist so the footer links resolve rather than dead-ending on "#", and
 * inventing legal language would be worse than saying plainly that it is being
 * written. The interim statements below describe what the product already does.
 */
export default function LegalPageContent({
  document,
}: {
  document: "privacy" | "terms";
}) {
  const { t } = useLanguage();
  const legal = t.legal;
  const heading =
    document === "privacy" ? legal.privacyHeading : legal.termsHeading;

  return (
    <div className="bg-(--schemes-bg)">
      <header className="border-b border-(--schemes-border) bg-(--schemes-surface) pt-nav">
        <div className="mx-auto w-full max-w-3xl px-4 pt-12 pb-10 sm:px-8">
          <Display as="h1" className="text-4xl lg:text-5xl xl:text-5xl">
            {heading}
          </Display>
        </div>
      </header>

      <div className="mx-auto w-full max-w-3xl px-4 py-10 sm:px-8">
        <div className="rounded-[0.625rem] border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) px-4 py-4">
          <p className="text-base font-semibold text-(--schemes-status-alert-text)">
            {legal.noticeTitle}
          </p>
          <Body className="mt-2 text-sm leading-[1.6] text-(--schemes-status-alert-text)">
            {legal.noticeBody}
          </Body>
        </div>

        <section className="pt-10">
          <Headline as="h2" className="mb-3 text-xl sm:text-2xl">
            {legal.interimHeading}
          </Headline>
          <Body className={cn("text-base leading-[1.6]", PROSE)}>
            {legal.interimBody}
          </Body>
        </section>

        <section className="pt-10">
          <Headline as="h2" className="mb-3 text-xl sm:text-2xl">
            {legal.partnerHeading}
          </Headline>
          <Body className={cn("text-base leading-[1.6]", PROSE)}>
            {legal.partnerBody}
          </Body>
        </section>

        <div className="pt-10">
          <Link
            href="/feedback"
            className={cn(productButtonOutlineBlue, productButtonDefault, "w-fit")}
          >
            {legal.contactCta}
          </Link>
        </div>
      </div>
    </div>
  );
}
