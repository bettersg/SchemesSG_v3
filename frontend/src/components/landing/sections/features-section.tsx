"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Building2,
  Check,
  ExternalLink,
  HeartPulse,
  Mail,
  MapPin,
  MousePointerClick,
  Phone,
  Search,
  Share2,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import SchemeLogo from "@/components/schemes/scheme-logo";
import BulletItem from "@/components/schemes/bullet-item";
import SectionLabel from "@/components/schemes/section-label";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import { SectionWrapper } from "@/components/landing/shared/section-wrapper";
import { plural } from "@lingui/core/macro";
import { Trans, useLingui } from "@lingui/react/macro";
import { useSchemeCount } from "@/lib/scheme-count";
import {
  productButtonOutlineNeutral,
  productButtonProminent,
  productButtonSolidAmber,
  productCard,
} from "@/lib/design-system/product-styles";
import { motionPreset, transition, viewport } from "@/lib/design-system/motion";
import { getSchemeCategoryChipClassName } from "@/lib/design-system/categories";
import { cn } from "@/lib/utils";

function useTutorialCopy() {
  const { t } = useLingui();
  return {
    composerLabel: t({
      message: "Describe your situation",
      comment: "Search box label in the feature walkthrough demo",
    }),
    categoryPrompts: [
      t({ message: "Financial Assistance" }),
      t({ message: "Family & Children" }),
      t({ message: "Health & Wellbeing" }),
    ],
    progress: [
      t({ message: "Understanding what support may fit your situation" }),
      t({ message: "Comparing schemes from trusted agencies" }),
    ],
    assistant: t({
      message:
        "I found schemes that may help with household expenses and childcare costs.",
    }),
    found: plural(10, {
      one: "# scheme found",
      other: "# schemes found",
    }),
    filterAll: t({
      message: "All matches",
      comment: "Filter chip in the demo results",
    }),
    filterAgency: "MSF",
    filterHealthcare: t({ message: "Health & Wellbeing" }),
    filters: t({ message: "Filter by agency or support type" }),
    detailTabs: [
      t({ message: "Overview" }),
      t({ message: "Who qualifies" }),
      t({ message: "How to apply" }),
      t({ message: "Agency details" }),
    ],
    previewSchemes: [
      {
        agency: t({ message: "Ministry of Social and Family Development" }),
        name: t({ message: "ComCare Short-to-Medium-Term Assistance" }),
        summary: t({
          message:
            "Financial support for households facing temporary difficulty with essential expenses.",
        }),
        typeLabel: t({ message: "Financial Assistance" }),
      },
      {
        agency: t({ message: "Ministry of Health" }),
        name: t({ message: "Community Health Assist Scheme (CHAS)" }),
        summary: t({
          message:
            "Subsidies for medical and dental care at participating clinics.",
        }),
        typeLabel: t({ message: "Health & Wellbeing" }),
      },
    ],
    detailAgency: t({ message: "Ministry of Social and Family Development" }),
    detailScheme: t({ message: "ComCare Short-to-Medium-Term Assistance" }),
    detailCategoryLabel: t({ message: "Financial Assistance" }),
    overview: t({
      message:
        "Short-term financial support for lower-income households facing temporary difficulty.",
    }),
    qualifies: [
      t({ message: "Singapore Citizens and Permanent Residents" }),
      t({ message: "Households needing help with essential expenses" }),
    ],
    apply: t({
      message:
        "Contact your nearest Social Service Office to discuss your circumstances and next steps.",
    }),
    serviceArea: t({
      message: "Service area",
      comment: "Field label on the demo scheme page",
    }),
    serviceAreaValue: t({
      message: "Available islandwide through Social Service Offices.",
    }),
    contacts: t({
      message: "Branches and contacts",
      comment: "Section heading on the demo scheme page",
    }),
    branchCentral: t({ message: "Central Singapore" }),
    branchWest: t({ message: "West Singapore" }),
    centralAddress: t({ message: "512 Thomson Road, Singapore 298136" }),
    westAddress: t({
      message: "Block 135 Jurong Gateway Road, Singapore 600135",
    }),
    phone: "1800 222 0000",
    email: "comcare@msf.gov.sg",
    visit: t({
      message: "Visit website",
      comment: "Button on the demo scheme page",
    }),
    share: t({
      message: "Share scheme",
      comment: "Button on the demo scheme page",
    }),
  };
}

type PreviewScheme = {
  agency: string;
  image: string;
  name: string;
  summary: string;
  typeKey: string;
  typeLabel: string;
};

const PREVIEW_SCHEME_META = [
  {
    image: "/landing/logos/msf.jpg",
    typeKey: "Financial Assistance",
  },
  {
    image: "/landing/logos/MOH.jpg",
    typeKey: "Health & Wellbeing",
  },
] as const;

function TutorialFrame({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-(--schemes-border) bg-(--schemes-bg) p-3 sm:p-5",
        className,
      )}
    >
      {children}
    </div>
  );
}

function ComposerPreview({ placeholder }: { placeholder: string }) {
  const TUTORIAL_COPY = useTutorialCopy();
  const { t } = useLingui();
  const [query, setQuery] = useState(placeholder);

  useEffect(() => {
    setQuery(placeholder);
  }, [placeholder]);

  return (
    <TutorialFrame>
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-(--schemes-blue-900)">
        <Search size={15} />
        <Trans comment="Label above the demo search input in the features tutorial">
          Describe your situation
        </Trans>
      </div>
      <div className="rounded-2xl border border-(--schemes-blue-100) bg-white p-3 shadow-sm focus-within:ring-2 focus-within:ring-(--schemes-blue-100)">
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={3}
          className="w-full resize-none bg-transparent text-sm leading-relaxed text-(--schemes-ink) outline-none placeholder:text-(--schemes-muted)"
        />
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            aria-label={t({
              comment: "Alt text for the submit button in the demo composer",
              message: "Search for this example",
            })}
            className="flex size-10 items-center justify-center rounded-full bg-(--schemes-amber-400) text-(--schemes-ink) transition-colors hover:bg-(--schemes-amber-500)"
          >
            <ArrowRight size={17} />
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {TUTORIAL_COPY.categoryPrompts.map((category) => (
          <button
            type="button"
            key={category}
            onClick={() => setQuery(category)}
            className="rounded-full border border-(--schemes-border) bg-white px-3 py-2 text-xs font-semibold text-(--schemes-ink-soft) transition-colors hover:border-(--schemes-blue-100) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)"
          >
            {category}
          </button>
        ))}
      </div>
    </TutorialFrame>
  );
}

function SearchProgressPreview() {
  const TUTORIAL_COPY = useTutorialCopy();
  return (
    <TutorialFrame className="flex min-h-72 flex-col justify-center">
      <div className="mb-4 flex items-center gap-2">
        {[
          ["/landing/logos/msf.jpg", "MSF"],
          ["/landing/logos/MOH.jpg", "MOH"],
          ["/landing/logos/hdb.jpg", "HDB"],
          ["/landing/logos/cpf.jpg", "CPF"],
        ].map(([src, agency]) => (
          <SchemeLogo key={agency} agency={agency} image={src} size="sm" />
        ))}
      </div>
      <div className="space-y-2">
        {TUTORIAL_COPY.progress.map((message, index) => (
          <div
            key={message}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium text-(--schemes-ink-soft)"
          >
            <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-(--schemes-blue-50) text-(--schemes-blue-600)">
              {index === TUTORIAL_COPY.progress.length - 1 ? (
                <Sparkles size={12} />
              ) : (
                <Check size={12} strokeWidth={3} />
              )}
            </span>
            {index === TUTORIAL_COPY.progress.length - 1 ? (
              <StatusTextShimmer>{message}</StatusTextShimmer>
            ) : (
              <span>{message}</span>
            )}
          </div>
        ))}
      </div>
      <div className="mt-4 max-w-[92%] rounded-2xl rounded-bl-md border border-(--schemes-border) bg-white px-3.5 py-3 text-sm leading-relaxed text-(--schemes-ink-soft)">
        {TUTORIAL_COPY.assistant}
      </div>
      <button
        type="button"
        className="mt-2 inline-flex w-fit items-center gap-2 rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) px-3 py-1.5 text-xs font-semibold text-(--schemes-status-info-text)"
      >
        <span className="size-1.5 rounded-full bg-(--schemes-blue-400)" />
        {TUTORIAL_COPY.found}
      </button>
    </TutorialFrame>
  );
}

function MiniSchemeCard({ scheme }: { scheme: PreviewScheme }) {
  return (
    <div className={cn(productCard, "flex min-h-36 flex-col p-3")}>
      <div className="mb-2 flex items-start gap-3">
        <SchemeLogo agency={scheme.agency} image={scheme.image} size="sm" />
        <div className="min-w-0 flex-1">
          <h4 className="font-(--font-head) text-sm font-semibold leading-snug text-(--schemes-blue-900)">
            {scheme.name}
          </h4>
          <p className="mt-1 truncate text-[11px] text-(--schemes-muted)">
            {scheme.agency}
          </p>
        </div>
      </div>
      <p className="line-clamp-2 text-xs leading-relaxed text-(--schemes-ink-soft)">
        {scheme.summary}
      </p>
      <div className="mt-auto pt-3">
        <span
          className={getSchemeCategoryChipClassName(
            scheme.typeKey,
            "px-2 py-0.5 text-[10px] font-semibold",
          )}
        >
          {scheme.typeLabel}
        </span>
      </div>
    </div>
  );
}

function ResultsPreview() {
  const TUTORIAL_COPY = useTutorialCopy();
  const [filter, setFilter] = useState<"all" | "msf" | "health">("all");
  const previewSchemes: PreviewScheme[] = TUTORIAL_COPY.previewSchemes.map(
    (scheme, index) => ({
      ...scheme,
      ...PREVIEW_SCHEME_META[index],
    }),
  );
  const schemes =
    filter === "msf"
      ? previewSchemes.slice(0, 1)
      : filter === "health"
        ? previewSchemes.slice(1)
        : previewSchemes;

  const filters = [
    { id: "all" as const, label: TUTORIAL_COPY.filterAll, icon: Search },
    { id: "msf" as const, label: TUTORIAL_COPY.filterAgency, icon: Building2 },
    {
      id: "health" as const,
      label: TUTORIAL_COPY.filterHealthcare,
      icon: HeartPulse,
    },
  ];

  return (
    <TutorialFrame className="p-0">
      <div className="border-b border-(--schemes-border) bg-white px-3 py-3">
        <p className="text-sm font-semibold text-(--schemes-blue-600)">
          {TUTORIAL_COPY.found}
        </p>
        <p className="mt-0.5 text-xs text-(--schemes-muted)">
          {TUTORIAL_COPY.filters}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {filters.map(({ id, label, icon: Icon }) => (
            <button
              type="button"
              key={id}
              onClick={() => setFilter(id)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors",
                filter === id
                  ? "border-(--schemes-blue-100) bg-(--schemes-blue-50) text-(--schemes-blue-600)"
                  : "border-(--schemes-border-neutral) bg-white text-(--schemes-muted) hover:border-(--schemes-blue-100) hover:text-(--schemes-blue-600)",
              )}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </div>
      </div>
      <div className="grid gap-3 pt-3 sm:grid-cols-2">
        {schemes.map((scheme) => (
          <MiniSchemeCard key={scheme.name} scheme={scheme} />
        ))}
      </div>
    </TutorialFrame>
  );
}

function DetailPreview() {
  const TUTORIAL_COPY = useTutorialCopy();
  const [activeTab, setActiveTab] = useState(0);

  return (
    <TutorialFrame className="p-0">
      <div className="border-b border-(--schemes-border-neutral) bg-white p-4">
        <div className="flex items-center gap-3">
          <SchemeLogo
            agency={TUTORIAL_COPY.detailAgency}
            image="/landing/logos/msf.jpg"
            size="md"
          />
          <div className="min-w-0">
            <p className="text-[11px] font-semibold text-(--schemes-muted)">
              {TUTORIAL_COPY.detailAgency}
            </p>
            <h4 className="mt-1 font-(--font-head) text-lg font-semibold leading-tight text-(--schemes-blue-900)">
              {TUTORIAL_COPY.detailScheme}
            </h4>
            <div className="mt-2">
              <span
                className={getSchemeCategoryChipClassName(
                  "Financial Assistance",
                  "px-2 py-0.5 text-[10px] font-semibold",
                )}
              >
                {TUTORIAL_COPY.detailCategoryLabel}
              </span>
            </div>
          </div>
        </div>
        <div className="no-scrollbar mt-4 flex gap-1 overflow-x-auto rounded-xl border border-(--schemes-border) bg-(--schemes-blue-50) p-1">
          {TUTORIAL_COPY.detailTabs.map((tab, index) => (
            <button
              type="button"
              key={tab}
              onClick={() => setActiveTab(index)}
              className={cn(
                "shrink-0 grow rounded-lg px-3 py-2 text-xs font-semibold text-(--schemes-blue-900) transition-colors",
                activeTab === index && "bg-white shadow-sm",
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
      <div className="min-h-36 bg-white p-4">
        {activeTab === 0 && (
          <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
            {TUTORIAL_COPY.overview}
          </p>
        )}
        {activeTab === 1 && (
          <div className="space-y-2">
            {TUTORIAL_COPY.qualifies.map((item) => (
              <BulletItem key={item}>{item}</BulletItem>
            ))}
          </div>
        )}
        {activeTab === 2 && (
          <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
            {TUTORIAL_COPY.apply}
          </p>
        )}
        {activeTab === 3 && (
          <div className="space-y-5">
            <div>
              <SectionLabel>{TUTORIAL_COPY.serviceArea}</SectionLabel>
              <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
                {TUTORIAL_COPY.serviceAreaValue}
              </p>
            </div>
            <div>
              <SectionLabel>{TUTORIAL_COPY.contacts}</SectionLabel>
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  {
                    area: TUTORIAL_COPY.branchCentral,
                    address: TUTORIAL_COPY.centralAddress,
                  },
                  {
                    area: TUTORIAL_COPY.branchWest,
                    address: TUTORIAL_COPY.westAddress,
                  },
                ].map((contact) => (
                  <div
                    key={contact.area}
                    className="flex flex-col gap-2 rounded-xl border border-(--schemes-blue-100) bg-(--schemes-surface) p-3 text-xs text-(--schemes-muted)"
                  >
                    <p className="font-semibold tracking-wide text-(--schemes-blue-900) uppercase">
                      {contact.area}
                    </p>
                    <div className="flex items-start gap-2">
                      <MapPin
                        size={15}
                        strokeWidth={2}
                        className="mt-0.5 shrink-0"
                      />
                      <span>{contact.address}</span>
                    </div>
                    <div className="flex items-center gap-2 text-(--schemes-blue-600)">
                      <Phone size={15} strokeWidth={2} className="shrink-0" />
                      {TUTORIAL_COPY.phone}
                    </div>
                    <div className="flex items-center gap-2 break-all text-(--schemes-blue-600)">
                      <Mail size={15} strokeWidth={2} className="shrink-0" />
                      {TUTORIAL_COPY.email}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        <div className="mt-5 grid grid-cols-2 gap-2">
          <div
            aria-hidden="true"
            className={`${productButtonOutlineNeutral} ${productButtonProminent} pointer-events-none w-full`}
          >
            <Share2 size={14} strokeWidth={2} className="shrink-0" />
            {TUTORIAL_COPY.share}
          </div>
          <div
            aria-hidden="true"
            className={`${productButtonSolidAmber} ${productButtonProminent} pointer-events-none relative w-full`}
          >
            <ExternalLink size={14} strokeWidth={2} className="shrink-0" />
            {TUTORIAL_COPY.visit}
            <MousePointerClick
              size={32}
              strokeWidth={1.2}
              className="absolute right-2 bottom-2 fill-white text-(--schemes-blue-900) drop-shadow-sm"
            />
          </div>
        </div>
      </div>
    </TutorialFrame>
  );
}

function WalkthroughRow({
  step,
  title,
  description,
  preview,
  reverse = false,
}: {
  step: number;
  title: string;
  description: string;
  preview: React.ReactNode;
  reverse?: boolean;
}) {
  const { t } = useLingui();
  const reduceMotion = useReducedMotion();

  return (
    <motion.article
      initial={reduceMotion ? false : motionPreset.fadeInUpWalkthrough.initial}
      whileInView={
        reduceMotion ? undefined : motionPreset.fadeInUpWalkthrough.animate
      }
      viewport={viewport.default}
      transition={transition.richEntrance}
      className={`grid items-center gap-8 ${!reverse ? "md:grid-cols-[minmax(0,0.75fr)_minmax(0,1.25fr)]" : "md:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]"} md:gap-12`}
    >
      <div className={cn(reverse && "md:order-2")}>
        <div className="mb-4 flex size-9 items-center justify-center rounded-full bg-(--schemes-blue-50) text-sm font-semibold text-(--schemes-blue-600)">
          <span className="sr-only">
            {t({
              comment:
                "Screen-reader label for a numbered step in the feature walkthrough",
              message: `Step ${step}`,
            })}
          </span>
          <span aria-hidden="true">{step}</span>
        </div>
        <h3 className="font-(--font-head) text-2xl font-semibold leading-tight text-(--schemes-blue-900)">
          {title}
        </h3>
        <p className="mt-3 max-w-xl text-base leading-relaxed text-(--schemes-muted)">
          {description}
        </p>
      </div>
      <div className={cn(reverse && "md:order-1")}>{preview}</div>
    </motion.article>
  );
}

export function FeaturesSection() {
  const { t } = useLingui();
  const schemeCount = useSchemeCount();

  return (
    <SectionWrapper id="features" className="overflow-hidden bg-neutral-50">
      <motion.div
        className="mx-auto max-w-3xl text-center"
        initial={motionPreset.fadeInUpMd.initial}
        whileInView={motionPreset.fadeInUpMd.animate}
        viewport={viewport.default}
        transition={transition.entrance}
      >
        <h2 className="font-serif text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem]">
          <Trans>Tools that do the searching for you</Trans>
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          <Trans>
            From your first question to how to apply, in one place.
          </Trans>
        </p>
      </motion.div>

      <div className="mx-auto mt-12 max-w-5xl md:mt-16 flex flex-col gap-20 md:gap-24">
        <WalkthroughRow
          step={1}
          title={t`Find schemes that fit you`}
          description={t`Describe your situation in your own words. We find the schemes that fit best, without the jargon.`}
          preview={
            <ComposerPreview
              placeholder={t`I'm a single parent looking for financial assistance…`}
            />
          }
        />
        <WalkthroughRow
          step={2}
          title={t`How we find your matches`}
          description={t`Simply type your question, and Schemes.sg instantly scans more than ${schemeCount} government and community assistance programs to show you what help is available.`}
          preview={<SearchProgressPreview />}
          reverse
        />
        <WalkthroughRow
          step={3}
          title={t`Narrow down to the schemes that fit`}
          description={t`Use filters to narrow down schemes by agency, category, eligibility criteria, and the type of support you need.`}
          preview={<ResultsPreview />}
        />
        <WalkthroughRow
          step={4}
          title={t`Apply directly with the agency`}
          description={t`See who qualifies, what you get, and where to apply for each scheme.`}
          preview={<DetailPreview />}
          reverse
        />
      </div>
    </SectionWrapper>
  );
}
