"use client";

import styles from "./scheme-detail.module.css";
import { Scheme } from "@/types/types";
import { Link } from "@heroui/react";
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
import {
  productButtonLg,
  productButtonPrimaryBlue,
  productButtonSecondary,
  productCardPadded,
  productCardHeadingLg,
} from "@/lib/design-system/product-styles";
import PageShell from "@/components/layout/page-shell";

function MarkdownWrapper({ text }: { text: string }) {
  return (
    <div
      className={`${styles.showMarker} max-w-[68ch] text-base leading-relaxed text-(--schemes-ink-soft)`}
    >
      <Markdown>{text}</Markdown>
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
        productButtonSecondary,
        productButtonLg,
        "w-full",
        status === "failed"
          ? "border-(--schemes-status-alert-border)! text-(--schemes-status-alert-text)!"
          : "",
        className,
      )}
    >
      {status === "copied" ? (
        <>
          <Check size={14} strokeWidth={2} />
          Link copied
        </>
      ) : status === "failed" ? (
        <>
          <AlertCircle size={14} strokeWidth={2} />
          Copy failed, try again
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
      className={`${productButtonPrimaryBlue} ${productButtonLg} w-full no-underline hover:no-underline ${className ?? ""}`}
    >
      <ExternalLink size={14} strokeWidth={2} />
      Visit website
    </Link>
  );
}

type JumpAnchor = { id: string; label: string };

function buildJumpAnchors(scheme: Scheme): JumpAnchor[] {
  const anchors: JumpAnchor[] = [];
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
  const jumpAnchors = useMemo(() => buildJumpAnchors(scheme), [scheme]);
  const [activeAnchor, setActiveAnchor] = useState(jumpAnchors[0]?.id ?? "");
  const [stickyHeaderHidden, setStickyHeaderHidden] = useState(false);
  const [stickyHeaderOffset, setStickyHeaderOffset] = useState(208);
  const stickyHeaderRef = useRef<HTMLDivElement>(null);
  const lastScrollYRef = useRef(0);
  const lastUserScrollIntentAtRef = useRef(0);
  const lastUserScrollDirectionRef = useRef<"down" | "up" | null>(null);
  const lastTouchYRef = useRef<number | null>(null);
  const suppressScrollToggleUntilRef = useRef(0);
  const stickyHeaderHiddenRef = useRef(false);
  const activeScrollTargetRef = useRef<EventTarget | null>(null);
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

  useEffect(() => {
    setActiveAnchor(jumpAnchors[0]?.id ?? "");
  }, [jumpAnchors]);

  useEffect(() => {
    stickyHeaderHiddenRef.current = stickyHeaderHidden;
  }, [stickyHeaderHidden]);

  useEffect(() => {
    const header = stickyHeaderRef.current;
    if (!header) return;

    const updateOffset = () => {
      const height = Math.ceil(header.getBoundingClientRect().height);
      const nextOffset = height + 16;
      setStickyHeaderOffset(nextOffset);
      document.documentElement.style.setProperty(
        "--scheme-detail-sticky-offset",
        `${nextOffset}px`,
      );
    };

    updateOffset();

    const observer = new ResizeObserver(updateOffset);
    observer.observe(header);
    window.addEventListener("resize", updateOffset);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", updateOffset);
      document.documentElement.style.removeProperty(
        "--scheme-detail-sticky-offset",
      );
    };
  }, []);

  useEffect(() => {
    const markUserScrollIntent = (direction: "down" | "up") => {
      lastUserScrollIntentAtRef.current = Date.now();
      lastUserScrollDirectionRef.current = direction;
    };

    const markWheelScrollIntent = (event: WheelEvent) => {
      if (Math.abs(event.deltaY) < 2) return;
      markUserScrollIntent(event.deltaY > 0 ? "down" : "up");
    };

    const markTouchStart = (event: TouchEvent) => {
      lastTouchYRef.current = event.touches[0]?.clientY ?? null;
    };

    const markTouchScrollIntent = (event: TouchEvent) => {
      const nextY = event.touches[0]?.clientY;
      const previousY = lastTouchYRef.current;
      if (nextY == null || previousY == null) return;

      const delta = previousY - nextY;
      if (Math.abs(delta) >= 2) {
        markUserScrollIntent(delta > 0 ? "down" : "up");
      }
      lastTouchYRef.current = nextY;
    };

    const markKeyboardScrollIntent = (event: KeyboardEvent) => {
      if (["ArrowDown", "End", "PageDown", " "].includes(event.key)) {
        markUserScrollIntent("down");
      } else if (["ArrowUp", "Home", "PageUp"].includes(event.key)) {
        markUserScrollIntent("up");
      }
    };

    const setHeaderHidden = (nextHidden: boolean) => {
      if (stickyHeaderHiddenRef.current === nextHidden) return;
      stickyHeaderHiddenRef.current = nextHidden;
      suppressScrollToggleUntilRef.current = Date.now() + 360;
      setStickyHeaderHidden(nextHidden);
    };

    function getScrollMetrics(event: Event) {
      const target = event.target;

      if (
        target === document ||
        target === document.documentElement ||
        target === document.body
      ) {
        const scrollHeight = document.documentElement.scrollHeight;
        return {
          maxScrollTop: Math.max(scrollHeight - window.innerHeight, 0),
          scrollTop: window.scrollY,
          target,
        };
      }

      if (target instanceof Element) {
        return {
          maxScrollTop: Math.max(target.scrollHeight - target.clientHeight, 0),
          scrollTop: target.scrollTop,
          target,
        };
      }

      return {
        maxScrollTop: Math.max(
          document.documentElement.scrollHeight - window.innerHeight,
          0,
        ),
        scrollTop: window.scrollY,
        target,
      };
    }

    function onScroll(event: Event) {
      const { maxScrollTop, scrollTop, target } = getScrollMetrics(event);
      const scrollY = Math.max(scrollTop, 0);
      const isScrollable = maxScrollTop > 0;
      const now = Date.now();

      if (!isScrollable) return;

      if (activeScrollTargetRef.current !== target) {
        activeScrollTargetRef.current = target;
        lastScrollYRef.current = scrollY;
        return;
      }

      const distanceFromBottom = maxScrollTop - scrollY;
      const hasRecentUserScrollIntent =
        now - lastUserScrollIntentAtRef.current < 900;
      const intentDirection = lastUserScrollDirectionRef.current;

      if (
        window.innerWidth >= 768 ||
        now < suppressScrollToggleUntilRef.current ||
        !hasRecentUserScrollIntent ||
        !intentDirection
      ) {
        lastScrollYRef.current = scrollY;
        return;
      }

      if (scrollY <= 12) {
        setHeaderHidden(false);
      } else if (intentDirection === "down") {
        setHeaderHidden(true);
      } else if (intentDirection === "up" && distanceFromBottom > 24) {
        setHeaderHidden(false);
      }

      lastScrollYRef.current = scrollY;
    }

    window.addEventListener("wheel", markWheelScrollIntent, { passive: true });
    window.addEventListener("touchstart", markTouchStart, { passive: true });
    window.addEventListener("touchmove", markTouchScrollIntent, {
      passive: true,
    });
    window.addEventListener("keydown", markKeyboardScrollIntent);
    document.addEventListener("scroll", onScroll, {
      capture: true,
      passive: true,
    });

    return () => {
      window.removeEventListener("wheel", markWheelScrollIntent);
      window.removeEventListener("touchstart", markTouchStart);
      window.removeEventListener("touchmove", markTouchScrollIntent);
      window.removeEventListener("keydown", markKeyboardScrollIntent);
      document.removeEventListener("scroll", onScroll, { capture: true });
    };
  }, []);

  useEffect(() => {
    if (jumpAnchors.length <= 1) return;

    const sections = jumpAnchors
      .map((anchor) => document.getElementById(anchor.id))
      .filter((section): section is HTMLElement => Boolean(section));

    if (!sections.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visible?.target.id) {
          setActiveAnchor(visible.target.id);
        }
      },
      {
        root: null,
        rootMargin: `-${stickyHeaderOffset}px 0px -60% 0px`,
        threshold: [0.1, 0.4, 0.7],
      },
    );

    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [jumpAnchors, stickyHeaderOffset]);

  const sectionScrollMarginStyle = {
    scrollMarginTop: "var(--scheme-detail-sticky-offset, 224px)",
  } satisfies CSSProperties;

  return (
    <PageShell contentClassName="pb-24 md:pb-8">
      <div
        ref={stickyHeaderRef}
        className="sticky top-0 z-20 -mt-8 mb-8 ml-[calc(50%-50vw)] w-screen border-b border-(--schemes-border-neutral) bg-(--schemes-surface) px-4 sm:px-6 md:mx-auto md:w-full md:max-w-3xl"
      >
        <div
          className={clsx(
            "overflow-hidden py-3 transition-[max-height,opacity,transform,padding] duration-300 md:max-h-none md:translate-y-0 md:opacity-100",
            stickyHeaderHidden
              ? "max-md:max-h-0 max-md:-translate-y-full max-md:py-0 max-md:opacity-0"
              : "max-md:max-h-48 max-md:translate-y-0 max-md:opacity-100",
          )}
        >
          <div className="flex items-center justify-between gap-4 text-left">
            <div className="flex min-w-0 items-center gap-4 md:gap-5">
              <SchemeLogo
                agency={scheme.agency}
                image={scheme.image}
                size="header"
              />
              <div className="flex min-w-0 flex-col gap-2">
                {scheme.agency && (
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-(--schemes-muted)">
                    {scheme.agency}
                  </p>
                )}
                {scheme.schemeName && (
                  <h1 className="line-clamp-2 text-xl font-semibold leading-tight text-(--schemes-blue-900) md:line-clamp-1 md:text-2xl">
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
            className="border-t border-(--schemes-border-neutral) pt-3"
          >
            <ul className="no-scrollbar flex w-full gap-6 overflow-x-auto">
              {jumpAnchors.map((a) => (
                <li key={a.id} className="shrink-0">
                  <a
                    href={`#${a.id}`}
                    onClick={() => setActiveAnchor(a.id)}
                    className={clsx(
                      "block border-b-2 pb-2 text-[11px] font-semibold uppercase tracking-[0.14em] transition-colors hover:text-(--schemes-blue-600)",
                      activeAnchor === a.id
                        ? "border-(--schemes-blue-600) text-(--schemes-blue-600)"
                        : "border-transparent text-(--schemes-muted)",
                    )}
                  >
                    {a.label}
                  </a>
                </li>
              ))}
            </ul>
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
          className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}
          style={sectionScrollMarginStyle}
        >
          <h2 className={productCardHeadingLg}>Overview</h2>
          <div className="flex flex-col gap-6">
            <div>
              <SectionLabel>Scheme details</SectionLabel>
              <MarkdownWrapper text={scheme.description} />
            </div>
            {scheme.schemeType && scheme.schemeType.length > 0 && (
              <div>
                <SectionLabel>Scheme type</SectionLabel>
                <div className="flex flex-wrap gap-2">
                  {scheme.schemeType.map((t) => (
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
          className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}
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
          className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}
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
          className={`${productCardPadded} mx-auto mb-8 max-w-3xl`}
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
              <div>
                <SectionLabel>Branches and contacts</SectionLabel>
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
              </div>
            )}
          </div>
        </section>
      )}

      <StatusBanner
        title="Important Information"
        className="mx-auto mb-8 max-w-3xl p-6"
      >
        <p>
          Scheme details may change. Visit the official agency website for the
          latest eligibility, benefits, and application information.{" "}
          <Link
            href="/feedback"
            className="text-sm text-(--schemes-blue-600) hover:underline"
          >
            Help us improve with your feedback
          </Link>
          .
        </p>
      </StatusBanner>

      <div className="fixed right-0 bottom-0 left-0 z-30 border-t border-(--schemes-border-neutral) bg-(--schemes-surface) p-3 md:hidden">
        <div className="mx-auto grid max-w-sm grid-cols-2 gap-3">
          <ShareButton scheme={scheme} className="" />
          {scheme.link ? (
            <VisitWebsiteButton href={scheme.link} />
          ) : (
            <div aria-hidden="true" />
          )}
        </div>
      </div>
    </PageShell>
  );
}
