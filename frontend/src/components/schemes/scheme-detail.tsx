"use client";

import styles from "./scheme-detail.module.css";
import { Scheme } from "@/types/types";
import { Link } from "@heroui/react";
import Markdown from "react-markdown";
import { ReactNode, useEffect, useState } from "react";
import SchemeLogo from "@/components/schemes/scheme-logo";
import {
  Check,
  ExternalLink,
  Info,
  Mail,
  MapPin,
  Phone,
  Share2,
} from "lucide-react";
import {
  getSchemeCategoryChipClassName,
  normalizeSchemeCategory,
} from "@/lib/design-system/categories";
import {
  productButtonLg,
  productButtonPrimaryBlue,
  productButtonSecondary,
  productCardPadded,
  productHeading,
  productPageContent,
  productPageShell,
} from "@/lib/design-system/product-styles";
import { capitalize } from "@/lib/utils";

function Tag({ label }: { label: string }) {
  return (
    <span
      className={getSchemeCategoryChipClassName(
        label,
        "px-2.5 py-0.5 text-[11px] font-semibold",
      )}
    >
      {normalizeSchemeCategory(label)}
    </span>
  );
}

function BulletItem({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-2.5 text-sm text-(--schemes-ink-soft)">
      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-500" />
      <span className="leading-snug">{children}</span>
    </div>
  );
}

function MarkdownWrapper({ text }: { text: string }) {
  return (
    <div className={`${styles.showMarker} text-sm text-(--schemes-ink-soft)`}>
      <Markdown>{text}</Markdown>
    </div>
  );
}

function ShareButton({ scheme }: { scheme: Scheme }) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const url = typeof window !== "undefined" ? window.location.href : "";
    const shareData = {
      title: `${scheme.schemeName} - ${scheme.agency} | SchemesSG`,
      text: `
      ${scheme.schemeName} - ${scheme.agency} | Schemes.sg\n
      ${scheme.summary}\n
      ${scheme.description}\n
      Check out this scheme on SchemesSG`,
      url,
    };

    if (
      typeof navigator !== "undefined" &&
      typeof navigator.share === "function" &&
      (typeof navigator.canShare !== "function" ||
        navigator.canShare(shareData))
    ) {
      try {
        await navigator.share(shareData);
        return;
      } catch (err) {
        if ((err as DOMException)?.name === "AbortError") return;
      }
    }

    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("Clipboard write failed:", err);
      }
    }
  };

  return (
    <button
      type="button"
      onClick={handleShare}
      className={`${productButtonSecondary} ${productButtonLg} w-full max-w-50`}
    >
      {copied ? (
        <>
          <Check size={14} strokeWidth={2} />
          Link copied
        </>
      ) : (
        <>
          <Share2 size={14} strokeWidth={2} />
          Share scheme
        </>
      )}
    </button>
  );
}

function SectionLabel({
  color = "bg-(--schemes-blue-400)",
  children,
}: {
  color?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <span className={`h-2 w-2 rounded-[3px] ${color}`} />
      <h3 className="text-sm font-semibold text-(--schemes-blue-900)">
        {children}
      </h3>
    </div>
  );
}

function CardHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-4 text-base font-semibold text-(--schemes-blue-900)">
      {children}
    </h2>
  );
}

export default function SchemeDetail({ scheme }: { scheme: Scheme }) {
  return (
    <div className={productPageShell}>
      <div className={productPageContent}>
        <div className="mb-10 flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-between sm:gap-8">
          <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:text-left">
            <SchemeLogo agency={scheme.agency} image={scheme.image} size="lg" />
            <div className="flex flex-col items-center gap-4 sm:items-start">
              {scheme.agency && (
                <p className="text-sm font-semibold text-(--schemes-muted)">
                  {scheme.agency}
                </p>
              )}
              {scheme.schemeName && (
                <h1 className={productHeading}>{scheme.schemeName}</h1>
              )}
              {scheme.schemeType && scheme.schemeType.length > 0 && (
                <div className="flex flex-wrap justify-center gap-3 sm:justify-start">
                  {scheme.schemeType.map((t) => (
                    <Tag key={t} label={t} />
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex w-full flex-row flex-wrap justify-center gap-3 pt-1 sm:max-w-max sm:flex-col sm:pt-0">
            {scheme.link && (
              <Link
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className={`${productButtonPrimaryBlue} ${productButtonLg} max-w-50 w-full no-underline hover:no-underline`}
              >
                <ExternalLink size={14} strokeWidth={2} />
                Visit website
              </Link>
            )}
            <ShareButton scheme={scheme} />
          </div>
        </div>

        {scheme.description && (
          <div className={`${productCardPadded} mb-6`}>
            <CardHeading>Overview</CardHeading>
            <MarkdownWrapper text={scheme.description} />
          </div>
        )}

        <div className={`${productCardPadded} mb-6`}>
          <CardHeading>What this scheme covers</CardHeading>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-6 sm:flex-row">
              {scheme.targetAudience && scheme.targetAudience.length > 0 && (
                <div className="flex-1">
                    <SectionLabel color="bg-(--schemes-category-healthcare-border)">
                      Who qualifies
                    </SectionLabel>
                  <div className="flex flex-col gap-2">
                    {scheme.targetAudience.map((t) => (
                      <BulletItem key={t}>{t}</BulletItem>
                    ))}
                  </div>
                </div>
              )}
              {scheme.benefits && scheme.benefits.length > 0 && (
                <div className="flex-1">
                  <SectionLabel color="bg-(--schemes-category-financial-border)">
                    What you receive
                  </SectionLabel>
                  <div className="flex flex-col gap-2">
                    {scheme.benefits.map((b) => (
                      <BulletItem key={b}>{b}</BulletItem>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {scheme.eligibilityText && (
              <div>
                <SectionLabel color="bg-(--schemes-category-mental-border)">
                  Eligibility details
                </SectionLabel>
                <MarkdownWrapper text={scheme.eligibilityText} />
              </div>
            )}

            {scheme.howToApply && (
              <div>
                <SectionLabel color="bg-(--schemes-category-employment-border)">
                  How to apply
                </SectionLabel>
                <MarkdownWrapper text={scheme.howToApply} />
              </div>
            )}
          </div>
        </div>

        {(scheme.serviceArea ||
          (scheme.contact && scheme.contact.length > 0)) && (
          <div className={`${productCardPadded} mb-6`}>
            <CardHeading>Agency details</CardHeading>
            <div className="flex flex-col gap-6">
              {scheme.serviceArea && (
                <div>
                  <SectionLabel color="bg-(--schemes-category-housing-border)">
                    Service area
                  </SectionLabel>
                  <p className="text-sm text-(--schemes-muted)">
                    {scheme.serviceArea}
                  </p>
                </div>
              )}

              {scheme.contact && scheme.contact.length > 0 && (
                <div>
                  <SectionLabel color="bg-(--schemes-category-eldercare-border)">
                    Branches and contacts
                  </SectionLabel>
                  <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                    {scheme.contact.map((c, i) => (
                      <div
                        key={i}
                        className="flex flex-col gap-1.5 rounded-xl border border-(--schemes-border) bg-(--schemes-bg) p-3.5 text-sm text-(--schemes-muted)"
                      >
                        {c.planningArea && (
                          <p className="text-xs font-semibold tracking-wide text-(--schemes-blue-900) uppercase">
                            {c.planningArea}
                          </p>
                        )}
                        {c.address && (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${scheme.schemeName} ${c.address}`)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-(--schemes-muted) hover:text-(--schemes-blue-600)"
                          >
                            <MapPin
                              size={16}
                              strokeWidth={2}
                              className="shrink-0"
                            />{" "}
                            {c.address ??
                              `${capitalize(c.planningArea ? c.planningArea.toLowerCase() : scheme.agency)} branch`}
                          </a>
                        )}
                        {c.phones?.map((p) => (
                          <a
                            key={p}
                            href={`tel:${p}`}
                            className="flex items-center gap-2 text-(--schemes-blue-600) hover:underline"
                          >
                            <Phone
                              size={16}
                              strokeWidth={2}
                              className="shrink-0"
                            />{" "}
                            {p}
                          </a>
                        ))}
                        {c.emails?.map((e) => (
                          <a
                            key={e}
                            href={`mailto:${e}`}
                            className="flex items-center gap-2 break-all text-(--schemes-blue-600) hover:underline"
                          >
                            <Mail
                              size={16}
                              strokeWidth={2}
                              className="shrink-0"
                            />{" "}
                            {e}
                          </a>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <section className="mb-8 rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4">
          <div className="flex items-start gap-3">
            <Info
              size={18}
              strokeWidth={2}
              className="mt-0.5 shrink-0 text-(--schemes-status-info-text)"
            />
            <div>
              <h3 className="mb-1 text-sm font-semibold text-(--schemes-status-info-text)">
                Important Information
              </h3>
              <p className="text-sm text-(--schemes-muted)">
                Scheme details may change. Visit the official agency website for
                the latest eligibility, benefits, and application information.{" "}
                <Link
                  href="/feedback"
                  className="text-sm text-(--schemes-blue-600) hover:underline"
                >
                  Help us improve with your feedback
                </Link>
                .
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
