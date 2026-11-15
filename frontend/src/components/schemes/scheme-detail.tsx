"use client";

import styles from "./scheme-detail.module.css";
import { Scheme } from "@/types/types";
import { Link, ScrollShadow } from "@heroui/react";
import Markdown from "react-markdown";
import { CSSProperties, useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import SchemeLogo from "@/components/schemes/scheme-logo";
import CategoryTag from "@/components/schemes/category-tag";
import SectionLabel from "@/components/schemes/section-label";
import BulletItem from "@/components/schemes/bullet-item";
import AgencyContactCard from "@/components/schemes/agency-contact-card";
import StatusBanner from "@/components/feedback/status-banner";
import { AlertCircle, Check, ExternalLink, Share2 } from "lucide-react";
import { track } from "@/lib/analytics";
import { Trans, useLingui } from "@lingui/react/macro";
import { msg } from "@lingui/core/macro";
import type { I18n } from "@lingui/core";
import { CATEGORY_LABELS } from "@/lib/design-system/category-labels";
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
import {
  getSchemeCategory,
  resolveSchemeCategory,
} from "@/lib/design-system/categories";
import { getCatalogCategoryPath } from "@/lib/catalog-seo";
import NextLink from "next/link";
import { ChevronRight } from "lucide-react";
import {
  type SchemeDetailAnchor,
  useSchemeDetailStickyOffset,
  useSchemeSectionNavigation,
} from "@/hooks/use-scheme-detail-navigation";
import { useHideOnScroll } from "@/hooks/use-hide-on-scroll";
import FeedbackPrompt from "@/components/feedback/feedback-prompt";
import {
  cssTransition,
  timeout as motionTimeout,
} from "@/lib/design-system/motion";
import { Footer } from "@/components/layout/footer";

// Scheme descriptions sometimes use literal bullet glyphs (• ● ‣ ·) on their
// own blank-line-separated lines instead of Markdown list syntax, which
// react-markdown renders as standalone paragraphs. Rewrite them into real list
// items so they render as one tight <ul>.
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
      className={`${styles.showMarker} text-base leading-relaxed text-(--schemes-ink-soft)`}
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
    setTimeout(() => setStatus("idle"), motionTimeout.shareStatusResetMs);
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
        track("scheme_shared", { share_outcome: "web_share" });
        return;
      } catch (err) {
        if ((err as DOMException)?.name === "AbortError") {
          track("scheme_shared", { share_outcome: "dismissed" });
          return;
        }
      }
    }

    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(url);
        flash("copied");
        track("scheme_shared", { share_outcome: "clipboard" });
        return;
      } catch (err) {
        console.error("Clipboard write failed:", err);
      }
    }

    flash("failed");
    track("scheme_shared", { share_outcome: "failed" });
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
          <Trans comment="Share button: the link was copied to clipboard">
            Link copied
          </Trans>
        </>
      ) : status === "failed" ? (
        <>
          <AlertCircle size={14} strokeWidth={2} className="shrink-0" />
          <Trans comment="Share button: the clipboard copy failed">
            Copy failed, try again
          </Trans>
        </>
      ) : (
        <>
          <Share2 size={14} strokeWidth={2} className="shrink-0" />
          <Trans comment="Button: share this scheme page">Share scheme</Trans>
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
      className={`${productButtonSolidAmber} ${productButtonProminent} w-full whitespace-normal text-center no-underline hover:no-underline ${className ?? ""}`}
    >
      <ExternalLink size={14} strokeWidth={2} className="shrink-0" />
      <Trans comment="Button: open the scheme's official website in a new tab">
        Visit website
      </Trans>
    </Link>
  );
}

function buildJumpAnchors(
  scheme: Scheme,
  i18n: I18n,
): SchemeDetailAnchor[] {
  const anchors: SchemeDetailAnchor[] = [];
  if (scheme.description)
    anchors.push({
      id: "overview",
      label: i18n._(
        msg({
          message: "Overview",
          comment: "Tab label: summary and category section on a scheme page",
        }),
      ),
    });
  const hasQualifies =
    (scheme.targetAudience && scheme.targetAudience.length > 0) ||
    (scheme.benefits && scheme.benefits.length > 0) ||
    scheme.eligibilityText;
  if (hasQualifies)
    anchors.push({
      id: "qualifies",
      label: i18n._(
        msg({
          message: "Who qualifies",
          comment: "Tab label: eligibility requirements section on a scheme page",
        }),
      ),
    });
  if (scheme.howToApply)
    anchors.push({
      id: "how-to-apply",
      label: i18n._(
        msg({
          message: "How to apply",
          comment: "Tab label: application steps section on a scheme page",
        }),
      ),
    });
  if (scheme.serviceArea || (scheme.contact && scheme.contact.length > 0)) {
    anchors.push({
      id: "agency",
      label: i18n._(
        msg({
          message: "Agency details",
          comment: "Tab label: agency contact and location section on a scheme page",
        }),
      ),
    });
  }
  return anchors;
}

export default function SchemeDetail({ scheme }: { scheme: Scheme }) {
  const { t, i18n } = useLingui();
  const hasCategory = (type: string) => getSchemeCategory(type) !== undefined;
  const sortedTypes = [...scheme.schemeType].sort((a, b) => {
    return Number(hasCategory(b)) - Number(hasCategory(a));
  });

  // Keyed on the scheme id, so navigating between schemes in a session reports
  // each one once rather than only the first.
  useEffect(() => {
    track("view_item", {
      items: [
        {
          item_id: scheme.schemeId,
          item_name: scheme.schemeName,
          item_category: sortedTypes[0],
        },
      ],
    });
  }, [scheme.schemeId, scheme.schemeName, sortedTypes]);

  const jumpAnchors = useMemo(
    () => buildJumpAnchors(scheme, i18n),
    // The labels are translated here, so a language switch has to rebuild them.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [scheme, i18n, i18n.locale],
  );
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
    <PageShell
      contentClassName="pb-8"
      footer={
        // The fixed mobile action bar overlays the end of the page, so the
        // footer carries that clearance in its own colour.
        <div className="bg-neutral-950 pb-24 md:pb-0">
          <Footer />
        </div>
      }
    >
      <div
        ref={stickyHeaderRef}
        // Full-bleed on mobile, so the band carries its own inset.
        className="sticky top-0 z-20 -mt-8 mb-8 ml-[calc(50%-50vw)] w-screen border-b border-(--schemes-border-neutral) bg-(--schemes-surface) px-3 md:mx-auto md:w-full md:max-w-3xl"
      >
        <div
          className={clsx(
            // pt only. The jump nav below owns its own top padding, so this
            // row must not also contribute a bottom gap.
            "overflow-hidden pt-3 md:max-h-none md:translate-y-0 md:opacity-100",
            cssTransition.disclosureState,
            "flex flex-col gap-3",
            stickyHeaderHidden
              ? "max-md:max-h-0 max-md:-translate-y-full max-md:pt-0 max-md:opacity-0"
              : "max-md:translate-y-0 max-md:opacity-100",
          )}
        >
          <div className="flex items-center justify-between gap-4 text-left">
            <div className="flex min-w-0 items-center gap-4 md:gap-5">
              {/* Same src, so the second img is a cache hit, not a fetch. */}
              <div className="md:hidden">
                <SchemeLogo
                  agency={scheme.agency}
                  image={scheme.image}
                  size="lg"
                />
              </div>
              <div className="hidden md:block">
                <SchemeLogo
                  agency={scheme.agency}
                  image={scheme.image}
                  size="xl"
                />
              </div>
              <div className="flex min-w-0 flex-col gap-2">
                {(() => {
                  const category = resolveSchemeCategory(scheme.schemeType);
                  if (category) {
                    return (
                      <nav
                        aria-label={t({
                          message: "Breadcrumb",
                          comment: "Aria label for the breadcrumb navigation at the top of the scheme page",
                        })}
                        className="flex items-center gap-1 text-xs text-(--schemes-muted)"
                      >
                        <NextLink
                          href="/catalog"
                          className="transition-colors hover:text-(--schemes-blue-600)"
                        >
                          <Trans comment="Breadcrumb: link to the main catalog page">
                            Catalogue
                          </Trans>
                        </NextLink>
                        <ChevronRight size={12} strokeWidth={2} aria-hidden />
                        <NextLink
                          href={getCatalogCategoryPath(category)}
                          className="transition-colors hover:text-(--schemes-blue-600)"
                        >
                          {i18n._(CATEGORY_LABELS[category])}
                        </NextLink>
                      </nav>
                    );
                  }
                  return null;
                })()}
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
            aria-label={t({
              message: "On this page",
              comment: "Aria label for the section navigation tabs on a scheme page",
            })}
            // Owns top and bottom padding: the hero above animates its own to 0 on scroll.
            className={clsx(
              "py-3",
              cssTransition.borderState,
              stickyHeaderHidden && "max-md:border-transparent",
            )}
          >
            <ScrollShadow
              orientation="horizontal"
              className="w-full touch-pan-x overflow-x-auto overflow-y-hidden overscroll-x-contain p-1 sm:overflow-x-visible"
              hideScrollBar
              size={20}
            >
              <div
                className={`${productSegmentedList} flex w-max min-w-full gap-1 p-1 sm:w-full`}
              >
                {jumpAnchors.map((anchor) => {
                  const isActive = activeAnchor === anchor.id;
                  return (
                    <a
                      key={anchor.id}
                      href={`#${anchor.id}`}
                      aria-current={isActive ? "location" : undefined}
                      onClick={(event) => {
                        event.preventDefault();
                        selectAnchor(anchor.id);
                      }}
                      className={clsx(
                        productSegmentedTab,
                        "inline-flex min-h-10 items-center justify-center whitespace-nowrap px-3 py-2 no-underline transition-[background-color,box-shadow] hover:bg-white/60 hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--schemes-blue-400) sm:min-w-0 sm:flex-1 sm:whitespace-normal sm:text-center sm:leading-snug",
                        isActive && productSegmentedIndicator,
                      )}
                    >
                      {anchor.label}
                    </a>
                  );
                })}
              </div>
            </ScrollShadow>
          </nav>
        )}
      </div>

      {scheme.status === "inactive" && (
        <StatusBanner
          variant="alert"
          title={t({
            message: "We couldn't reach this scheme's website",
            comment: "Alert banner title: the scheme's URL failed health check",
          })}
          className="mx-auto mb-8 max-w-3xl"
        >
          <p>
            <Trans>
              Its official link failed our last check, so the details below may
              be out of date. Contact the agency to confirm before you apply.
            </Trans>
          </p>
        </StatusBanner>
      )}

      {!hasDetail && (
        <section className="mb-10 rounded-xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-6">
          <p className="mb-3 text-sm leading-relaxed text-(--schemes-status-info-text)">
            <Trans>
              We don&apos;t have detailed information for this scheme yet. The
              agency website has the full picture, including eligibility and how
              to apply.
            </Trans>
          </p>
          {scheme.link && (
            <Link
              href={scheme.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-(--schemes-blue-600) hover:underline"
            >
              <Trans>Visit the agency website →</Trans>
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
          <h2 className={productCardHeadingLg}>
            <Trans comment="Section heading: summary and category">
              Overview
            </Trans>
          </h2>
          <div className="flex flex-col gap-6">
            <MarkdownWrapper text={scheme.description} />
            {sortedTypes && sortedTypes.length > 0 && (
              <div>
                <SectionLabel>
                  <Trans comment="Section label: the category tags for a scheme">
                    Scheme type
                  </Trans>
                </SectionLabel>
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
          <h2 className={productCardHeadingLg}>
            <Trans comment="Section heading: who can apply for this scheme">
              Who qualifies
            </Trans>
          </h2>

          <div className="flex flex-col gap-8">
            <div className="flex flex-col gap-6 lg:flex-row">
              {scheme.targetAudience && scheme.targetAudience.length > 0 && (
                <div className="flex-1">
                  <SectionLabel>
                    <Trans comment="Section label: the groups who are eligible">
                      Eligibility groups
                    </Trans>
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
                  <SectionLabel>
                    <Trans comment="Section label: the benefits provided">
                      What you receive
                    </Trans>
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
                <SectionLabel>
                  <Trans comment="Section label: detailed eligibility criteria">
                    Eligibility details
                  </Trans>
                </SectionLabel>
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
          <h2 className={productCardHeadingLg}>
            <Trans comment="Section heading: instructions for applying">
              How to apply
            </Trans>
          </h2>
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
          <h2 className={productCardHeadingLg}>
            <Trans comment="Section heading: agency contact and location">
              Agency details
            </Trans>
          </h2>
          <div className="flex flex-col gap-6">
            {scheme.serviceArea && (
              <div>
                <SectionLabel>
                  <Trans comment="Section label: geographic coverage">
                    Service area
                  </Trans>
                </SectionLabel>
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
        title={t({
          message: "Important Information",
          comment: "Info banner heading: disclaimer about scheme accuracy",
        })}
        className="mx-auto mb-8 max-w-3xl p-6"
      >
        <div className="flex flex-col gap-4">
          <p>
            <Trans>
              Scheme details may change. Check the official agency website for
              the latest eligibility, benefits, and application information.
            </Trans>
          </p>
          <div className="flex flex-col gap-3">
            <p>
              <Trans>
                Help keep Schemes.sg accurate by correcting this listing or
                contributing a new scheme.
              </Trans>
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
