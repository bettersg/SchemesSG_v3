"use client";

import styles from "./scheme-detail.module.css";
import { Scheme } from "@/types/types";
import { Link } from "@heroui/react";
import Markdown from "react-markdown";
import { ReactNode, useEffect, useState } from "react";
import SchemeLogo from "@/components/schemes/scheme-logo";
import {
  ArrowRight,
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
  productButtonPrimary,
  productButtonSecondary,
  productCardPadded,
  productHeading,
  productPageContent,
  productPageShell,
} from "@/lib/design-system/product-styles";
import { capitalize } from "@/lib/utils";
import clsx from "clsx";

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

function CheckItem({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-start gap-2.5 text-sm text-(--schemes-ink-soft)">
      <div
        className={clsx(
          "mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center",
          "rounded-[5px] border border-(--schemes-blue-100) bg-(--schemes-blue-50)",
        )}
      >
        <Check size={9} strokeWidth={2} className="text-(--schemes-blue-600)" />
      </div>
      <span className="leading-snug">{children}</span>
    </div>
  );
}

function MarkdownWrapper({ text }: { text: string }) {
  return (
    <div className={`${styles.showMarker} text-sm text-(--schemes-muted)`}>
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
      className={`${productButtonSecondary} ${productButtonLg}`}
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
  color,
  children,
}: {
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <div className={`h-2 w-2 rounded-[3px] ${color}`} />
      <span className="text-[10px] font-semibold tracking-[0.08em] text-(--schemes-muted) uppercase">
        {children}
      </span>
    </div>
  );
}

export default function SchemeDetail({ scheme }: { scheme: Scheme }) {
  return (
    <div className={productPageShell}>
      <div className={productPageContent}>
        <div className="mb-8 flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:text-left">
          <SchemeLogo agency={scheme.agency} image={scheme.image} size="lg" />
          <div className="flex flex-col items-center gap-2 sm:items-start">
            {scheme.agency && (
              <h1 className={productHeading}>{scheme.agency}</h1>
            )}
            {scheme.schemeName && (
              <p className="text-base text-(--schemes-muted)">
                {scheme.schemeName}
              </p>
            )}
            {scheme.link && (
              <Link
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-semibold text-(--schemes-blue-600) transition-colors hover:text-(--schemes-blue-800)"
              >
                Find out more
                <ExternalLink size={14} strokeWidth={2} />
              </Link>
            )}
          </div>
        </div>

        {scheme.description && (
          <div className={`${productCardPadded} mb-6`}>
            <SectionLabel color="bg-(--schemes-blue-400)">About</SectionLabel>
            <MarkdownWrapper text={scheme.description} />
          </div>
        )}

        <div className={`${productCardPadded} mb-6`}>
          <div className="mb-5 flex items-center gap-2">
            <span className="text-lg font-semibold text-(--schemes-blue-900)">
              Details
            </span>
          </div>

          <div className="flex flex-col gap-8 lg:flex-row">
            <div className="flex flex-[2] flex-col gap-6">
              <div className="flex flex-col gap-6 sm:flex-row">
                {scheme.targetAudience && scheme.targetAudience.length > 0 && (
                  <div className="flex-1">
                    <SectionLabel color="bg-(--schemes-amber-400)">
                      Who qualifies
                    </SectionLabel>
                    <div className="flex flex-col gap-2">
                      {scheme.targetAudience.map((t) => (
                        <CheckItem key={t}>{t}</CheckItem>
                      ))}
                    </div>
                  </div>
                )}
                {scheme.benefits && scheme.benefits.length > 0 && (
                  <div className="flex-1">
                    <SectionLabel color="bg-(--schemes-blue-400)">
                      What you receive
                    </SectionLabel>
                    <div className="flex flex-col gap-2">
                      {scheme.benefits.map((b) => (
                        <CheckItem key={b}>{b}</CheckItem>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {scheme.eligibilityText && (
                <div>
                  <SectionLabel color="bg-(--schemes-blue-400)">
                    Eligibility
                  </SectionLabel>
                  <MarkdownWrapper text={scheme.eligibilityText} />
                </div>
              )}

              {scheme.howToApply && (
                <div>
                  <SectionLabel color="bg-(--schemes-blue-400)">
                    How to apply
                  </SectionLabel>
                  <MarkdownWrapper text={scheme.howToApply} />
                </div>
              )}
            </div>

            <div className="flex flex-1 flex-col gap-6">
              {scheme.schemeType && scheme.schemeType.length > 0 && (
                <div>
                  <SectionLabel color="bg-(--schemes-blue-400)">
                    Type
                  </SectionLabel>
                  <div className="flex flex-wrap gap-1.5">
                    {scheme.schemeType.map((t) => (
                      <Tag key={t} label={t} />
                    ))}
                  </div>
                </div>
              )}

              {scheme.serviceArea && (
                <div>
                  <SectionLabel color="bg-(--schemes-muted-light)">
                    Service area
                  </SectionLabel>
                  <p className="text-sm text-(--schemes-muted)">
                    {scheme.serviceArea}
                  </p>
                </div>
              )}

              {scheme.contact && scheme.contact.length > 0 && (
                <div>
                  <SectionLabel color="bg-(--schemes-muted-light)">
                    Branches
                  </SectionLabel>
                  <div className="flex flex-col gap-3">
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

          <div className="mt-8 flex flex-wrap justify-center gap-3 border-t border-(--schemes-border) pt-5 sm:justify-end">
            <ShareButton scheme={scheme} />
            {scheme.link && (
              <Link
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className={`${productButtonPrimary} ${productButtonLg}`}
              >
                <ArrowRight size={14} strokeWidth={2} />
                Visit agency website
              </Link>
            )}
          </div>
        </div>

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
                We strive to provide accurate information about assistance
                schemes in Singapore. Program details may change over time, so
                please visit the official website for the most current
                information.{" "}
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
