"use client";

import styles from "./scheme-detail.module.css";
import { Scheme } from "@/types/types";
import { Link, ScrollShadow, Tabs } from "@heroui/react";
import Markdown from "react-markdown";
import { CSSProperties, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import SchemeLogo from "@/components/schemes/scheme-logo";
import CategoryTag from "@/components/schemes/category-tag";
import SectionLabel from "@/components/schemes/section-label";
import BulletItem from "@/components/schemes/bullet-item";
import AgencyContactCard from "@/components/schemes/agency-contact-card";
import StatusBanner from "@/components/feedback/status-banner";
import { AlertCircle, Check, ExternalLink, Share2 } from "lucide-react";
import {
  productButtonOutlineNeutral,
  productButtonProminent,
  productButtonSolidAmber,
  productCardHeadingLg,
  productSegmentedIndicator,
  productSegmentedList,
  productSegmentedTab,
} from "@/lib/design-system/product-styles";
import PageShell from "@/components/layout/page-shell";
import { getSchemeCategory } from "@/lib/design-system/categories";
import {
  type SchemeDetailAnchor,
  useSchemeDetailStickyOffset,
  useSchemeSectionNavigation,
} from "@/hooks/use-scheme-detail-navigation";
import { useHideOnScroll } from "@/hooks/use-hide-on-scroll";
import FeedbackPrompt from "@/components/feedback/feedback-prompt";

// Scheme descriptions sometimes use literal bullet glyphs (• ● ‣ ·) on their
// own lines instead of Markdown list syntax, and separate them with blank
// lines. react-markdown then renders each as a standalone <p>, so they get the
// same spacing as paragraphs and don't read as a grouped list. Normalize those
// lines into real Markdown list items (and drop the blank lines between them)
// so they render as a tight <ul> with proper markers and indentation.
function normalizeBulletMarkdown(text: string): string {
  const isBullet = (line: string) => /^\s*[•●‣·]\s+/.test(line);
  const toItem = (line: string) => line.replace(/^\s*[•●‣·]\s+/, "- ");
  const out: string[] = [];
  let prevWasBullet = false;

  for (const line of text.split("\n")) {
    if (isBullet(line)) {
      // Open the list with one blank line after a preceding paragraph; keep
      // consecutive bullets adjacent (no blank line) so the list stays tight.
      const prev = out[out.length - 1];
      if (!prevWasBullet && prev !== undefined && prev.trim() !== "") {
        out.push("");
      }
      out.push(toItem(line));
      prevWasBullet = true;
    } else if (line.trim() === "" && prevWasBullet) {
      // Swallow blank lines that merely separated bullets; keeps the list tight.
      continue;
    } else {
      // Close the list with a blank line before the following paragraph.
      if (prevWasBullet && line.trim() !== "") out.push("");
      out.push(line);
      prevWasBullet = false;
    }
  }
  return out.join("\n");
}

function MarkdownWrapper({ text }: { text: string }) {
  return (
    <div
      className={`${styles.showMarker} max-w-[68ch] text-base leading-relaxed text-(--schemes-ink-soft)`}
    >
      <Markdown>{normalizeBulletMarkdown(text)}</Markdown>
    </div>
  );
}

function ShareButton({
  scheme,
  className,
}: {
  scheme: Scheme;
  className: string;
}) {
  const [status, setStatus] = useState<"idle" | "copied" | "failed">("idle");

  const flash = (next: "copied" | "failed") => {
    setStatus(next);
    setTimeout(() => setStatus("idle"), 2000);
  };

  const handleShare = async () => {
    const url = typeof window !== "undefined" ? window.location.href : "";
    const shareData = {
      title: `${scheme.schemeName} - ${scheme.agency} | SchemesSG`,
      text: `
      ${scheme.schemeName} - ${scheme.agency} | Schemes.sg\n
      ${scheme.summary}\n
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
        flash("copied");
        return;
      } catch (err) {
        console.error("Clipboard write failed:", err);
      }
    }

    flash("failed");
  };

  return (
    <button
      type="button"
      onClick={handleShare}
      className={clsx(
        productButtonOutlineNeutral,
        productButtonProminent,
        "w-full",
        status === "failed"
          ? "border-(--schemes-status-alert-border)! text-(--schemes-status-alert-text)!"
          : "",
        className,
      )}
    >
      {status === "copied" ? (
        <>
          <Check size={14} strokeWidth={2} className="shrink-0" />
          Link copied
        </>
      ) : status === "failed" ? (
        <>
          <AlertCircle size={14} strokeWidth={2} className="shrink-0" />
          Copy failed, try again
        </>
      ) : (
        <>
          <Share2 size={14} strokeWidth={2} className="shrink-0" />
          Share scheme
        </>
      )}
    </button>
  );
}

function VisitWebsiteButton({
  href,
  className,
}: {
  href: string;
  className?: string;
}) {
  return (
    <Link
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={`${productButtonSolidAmber} ${productButtonProminent} w-full no-underline hover:no-underline ${className ?? ""}`}
    >
      <ExternalLink size={14} strokeWidth={2} className="shrink-0" />
      Visit website
    </Link>
  );
}

function buildJumpAnchors(scheme: Scheme): SchemeDetailAnchor[] {
  const anchors: SchemeDetailAnchor[] = [];
  if (scheme.description) anchors.push({ id: "overview", label: "Overview" });
  const hasQualifies =
    (scheme.targetAudience && scheme.targetAudience.length > 0) ||
    (scheme.benefits && scheme.benefits.length > 0) ||
    scheme.eligibilityText;
  if (hasQualifies) anchors.push({ id: "qualifies", label: "Who qualifies" });
  if (scheme.howToApply)
    anchors.push({ id: "how-to-apply", label: "How to apply" });
  if (scheme.serviceArea || (scheme.contact && scheme.contact.length > 0)) {
    anchors.push({ id: "agency", label: "Agency details" });
  }
  return anchors;
}

export default function SchemeDetail({ scheme }: { scheme: Scheme }) {
  const hasCategory = (type: string) => getSchemeCategory(type) !== undefined;
  const sortedTypes = [...scheme.schemeType].sort((a, b) => {
    return Number(hasCategory(b)) - Number(hasCategory(a));
  });

  const jumpAnchors = useMemo(() => buildJumpAnchors(scheme), [scheme]);
  const stickyHeaderRef = useRef<HTMLDivElement>(null);
  const { isHidden: stickyHeaderHidden } = useHideOnScroll();
  const stickyHeaderOffset = useSchemeDetailStickyOffset(stickyHeaderRef);
  const { activeAnchor, selectAnchor } = useSchemeSectionNavigation({
    anchors: jumpAnchors,
    stickyOffset: stickyHeaderOffset,
    headerRef: stickyHeaderRef,
  });
  const hasCoverage =
    (scheme.targetAudience && scheme.targetAudience.length > 0) ||
    (scheme.benefits && scheme.benefits.length > 0) ||
    Boolean(scheme.eligibilityText) ||
    Boolean(scheme.howToApply);
  const hasDetail =
    Boolean(scheme.description) ||
    (scheme.targetAudience && scheme.targetAudience.length > 0) ||
    (scheme.benefits && scheme.benefits.length > 0) ||
    Boolean(scheme.eligibilityText) ||
    Boolean(scheme.howToApply) ||
    Boolean(scheme.serviceArea) ||
    (scheme.contact && scheme.contact.length > 0);

  const sectionScrollMarginStyle = {
    scrollMarginTop: "var(--scheme-detail-sticky-offset, 224px)",
  } satisfies CSSProperties;

  return (
    <PageShell contentClassName="pb-24 md:pb-8">
      <div
        ref={stickyHeaderRef}
        className="sticky top-0 z-20 -mt-8 mb-8 ml-[calc(50%-50vw)] w-screen border-b border-(--schemes-border-neutral) bg-(--schemes-surface) md:mx-auto md:w-full md:max-w-3xl"
      >
        <div
          className={clsx(
            "overflow-hidden py-3 transition-[max-height,opacity,transform,padding] duration-300 md:max-h-none md:translate-y-0 md:opacity-100",
            "flex flex-col gap-3",
            stickyHeaderHidden
              ? "max-md:max-h-0 max-md:-translate-y-full max-md:py-0 max-md:opacity-0"
              : "max-md:translate-y-0 max-md:opacity-100",
          )}
        >
          <div className="flex items-center justify-between gap-4 text-left">
            <div className="flex min-w-0 items-center gap-4 md:gap-5">
              <SchemeLogo
                agency={scheme.agency}
                image={scheme.image}
                size="lg"
              />
              <div className="flex min-w-0 flex-col gap-2">
                {scheme.agency && (
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-(--schemes-muted)">
                    {scheme.agency}
                  </p>
                )}
                {scheme.schemeName && (
                  <h1 className="text-balance text-xl font-semibold leading-snug text-(--schemes-blue-900) md:text-2xl">
                    {scheme.schemeName}
                  </h1>
                )}
                {scheme.summary && (
                  <p className="line-clamp-2 max-w-2xl text-xs leading-relaxed text-(--schemes-ink-soft) md:text-sm">
                    {scheme.summary}
                  </p>
                )}
              </div>
            </div>

            <div className="hidden w-full max-w-52 flex-col gap-2 md:flex">
              {scheme.link && <VisitWebsiteButton href={scheme.link} />}
              <ShareButton scheme={scheme} className="" />
            </div>
          </div>
        </div>
        {jumpAnchors.length > 1 && (
          <nav
            aria-label="On this page"
            className={clsx(
              "transition-[border-color] duration-300",
              stickyHeaderHidden && "max-md:border-transparent",
            )}
          >
            <Tabs
              selectedKey={activeAnchor}
              onSelectionChange={(key) => selectAnchor(String(key))}
              className="w-full"
            >
              <Tabs.ListContainer>
                <ScrollShadow
                  orientation="horizontal"
                  className="w-full touch-pan-x overflow-x-auto overflow-y-hidden overscroll-x-contain sm:overflow-x-visible p-1"
                  hideScrollBar
                  size={20}
                >
                  <Tabs.List
                    aria-label="On this page"
                    className={`${productSegmentedList} w-max min-w-full sm:w-full`}
                  >
                    {jumpAnchors.map((anchor) => (
                      <Tabs.Tab
                        key={anchor.id}
                        id={anchor.id}
                        className={`${productSegmentedTab} whitespace-nowrap sm:flex-1`}
                      >
                        {anchor.label}
                        <Tabs.Indicator className={productSegmentedIndicator} />
                      </Tabs.Tab>
                    ))}
                  </Tabs.List>
                </ScrollShadow>
              </Tabs.ListContainer>
            </Tabs>
          </nav>
        )}
      </div>

      {!hasDetail && (
        <section className="mb-10 rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-6">
          <p className="mb-3 text-sm leading-relaxed text-(--schemes-status-info-text)">
            We don&apos;t have detailed information for this scheme yet. The
            agency website has the full picture, including eligibility and how
            to apply.
          </p>
          {scheme.link && (
            <Link
              href={scheme.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-(--schemes-blue-600) hover:underline"
            >
              Visit the agency website →
            </Link>
          )}
        </section>
      )}

      {scheme.description && (
        <section
          id="overview"
          className="mx-auto mb-10 max-w-3xl"
          style={sectionScrollMarginStyle}
        >
          <h2 className={productCardHeadingLg}>Overview</h2>
          <div className="flex flex-col gap-6">
            <MarkdownWrapper text={scheme.description} />
            {sortedTypes && sortedTypes.length > 0 && (
              <div>
                <SectionLabel>Scheme type</SectionLabel>
                <div className="flex flex-wrap gap-2">
                  {sortedTypes.map((t) => (
                    <CategoryTag key={t} label={t} size="md" />
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {hasCoverage && (
        <section
          id="qualifies"
          className="mx-auto mb-10 max-w-3xl"
          style={sectionScrollMarginStyle}
        >
          <h2 className={productCardHeadingLg}>Who qualifies</h2>

          <div className="flex flex-col gap-8">
            <div className="flex flex-col gap-6 lg:flex-row">
              {scheme.targetAudience && scheme.targetAudience.length > 0 && (
                <div className="flex-1">
                  <SectionLabel>Eligibility groups</SectionLabel>
                  <div className="flex flex-col gap-2">
                    {scheme.targetAudience.map((t) => (
                      <BulletItem key={t}>{t}</BulletItem>
                    ))}
                  </div>
                </div>
              )}
              {scheme.benefits && scheme.benefits.length > 0 && (
                <div className="flex-1">
                  <SectionLabel>What you receive</SectionLabel>
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
                <SectionLabel>Eligibility details</SectionLabel>
                <MarkdownWrapper text={scheme.eligibilityText} />
              </div>
            )}
          </div>
        </section>
      )}

      {scheme.howToApply && (
        <section
          id="how-to-apply"
          className="mx-auto mb-10 max-w-3xl"
          style={sectionScrollMarginStyle}
        >
          <h2 className={productCardHeadingLg}>How to apply</h2>
          <MarkdownWrapper text={scheme.howToApply} />
        </section>
      )}

      {(scheme.serviceArea ||
        (scheme.contact && scheme.contact.length > 0)) && (
        <section
          id="agency"
          className="mx-auto mb-10 max-w-3xl"
          style={sectionScrollMarginStyle}
        >
          <h2 className={productCardHeadingLg}>Agency details</h2>
          <div className="flex flex-col gap-6">
            {scheme.serviceArea && (
              <div>
                <SectionLabel>Service area</SectionLabel>
                <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
                  {scheme.serviceArea}
                </p>
              </div>
            )}

            {scheme.contact && scheme.contact.length > 0 && (
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                {scheme.contact.map((c, i) => (
                  <AgencyContactCard
                    key={i}
                    contact={c}
                    schemeName={scheme.schemeName}
                    agency={scheme.agency}
                  />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      <StatusBanner
        title="Important Information"
        className="mx-auto mb-8 max-w-3xl p-6"
      >
        <div className="flex flex-col gap-4">
          <p>
            Scheme details may change. Check the official agency website for the
            latest eligibility, benefits, and application information.
          </p>
          <div className="flex flex-col gap-3">
            <p>
              Help keep Schemes.sg accurate by correcting this listing or
              contributing a new scheme.
            </p>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <FeedbackPrompt
                variant="correction"
                schemeId={scheme.schemeId}
                schemeName={scheme.schemeName}
              />
              <FeedbackPrompt variant="general" />
            </div>
          </div>
        </div>
      </StatusBanner>

      <div className="fixed right-0 bottom-0 left-0 z-30 border-t border-(--schemes-border-neutral) bg-(--schemes-surface) p-3 md:hidden">
        <div className="mx-auto grid max-w-sm grid-cols-2 gap-3">
          <ShareButton scheme={scheme} className="h-full" />
          {scheme.link ? (
            <VisitWebsiteButton href={scheme.link} className="h-full" />
          ) : (
            <div aria-hidden="true" />
          )}
        </div>
      </div>
    </PageShell>
  );
}
