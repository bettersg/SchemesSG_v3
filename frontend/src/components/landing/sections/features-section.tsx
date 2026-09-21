"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  Building2,
  Check,
  ChevronDown,
  ExternalLink,
  HeartPulse,
  Mail,
  MapPin,
  MousePointer2,
  MousePointerClick,
  Phone,
  Search,
  Share2,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import SchemeLogo from "@/components/schemes/scheme-logo";
import BulletItem from "@/components/schemes/bullet-item";
import SectionLabel from "@/components/schemes/section-label";
import { StatusTextShimmer } from "@/components/chat/status-text-shimmer";
import { SectionWrapper } from "@/components/landing/shared/section-wrapper";
import { useLanguage } from "@/lib/landing-i18n";
import {
  productButtonDefault,
  productButtonOutlineBlue,
  productButtonOutlineNeutral,
  productButtonProminent,
  productButtonSolidAmber,
  productCard,
} from "@/lib/design-system/product-styles";
import {
  motionPreset,
  transition,
  viewport,
} from "@/lib/design-system/motion";
import { getSchemeCategoryChipClassName } from "@/lib/design-system/categories";
import { cn } from "@/lib/utils";
import type { Translations } from "@/lib/landing-i18n/types";

type TutorialCopy = Translations["features"]["tutorial"] & {
  submitExampleQuery: string;
};

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

function ComposerPreview({
  copy,
  placeholder,
}: {
  copy: TutorialCopy;
  placeholder: string;
}) {
  const [query, setQuery] = useState(placeholder);

  useEffect(() => {
    setQuery(placeholder);
  }, [placeholder]);

  return (
    <TutorialFrame>
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-(--schemes-blue-900)">
        <Search size={15} />
        {copy.composerLabel}
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
            aria-label={copy.submitExampleQuery}
            className="flex size-10 items-center justify-center rounded-full bg-(--schemes-amber-400) text-(--schemes-ink) transition-colors hover:bg-(--schemes-amber-500)"
          >
            <ArrowRight size={17} />
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {copy.categoryPrompts.map((category) => (
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

function SearchProgressPreview({ copy }: { copy: TutorialCopy }) {
  return (
    <TutorialFrame className="flex min-h-72 flex-col justify-center">
      <div className="mb-4 flex items-center gap-2">
        {[
          ["/landing/logos/msf.jpg", "MSF"],
          ["/landing/logos/MOH.jpg", "MOH"],
          ["/landing/logos/hdb.jpg", "HDB"],
          ["/landing/logos/cpf.jpg", "CPF"],
        ].map(([src, agency]) => (
          <SchemeLogo key={agency} agency={agency} image={src} />
        ))}
      </div>
      <div className="space-y-2">
        {copy.progress.map((message, index) => (
          <div
            key={message}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium text-(--schemes-ink-soft)"
          >
            <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-(--schemes-blue-50) text-(--schemes-blue-600)">
              {index === copy.progress.length - 1 ? (
                <Sparkles size={12} />
              ) : (
                <Check size={12} strokeWidth={3} />
              )}
            </span>
            {index === copy.progress.length - 1 ? (
              <StatusTextShimmer>{message}</StatusTextShimmer>
            ) : (
              <span>{message}</span>
            )}
          </div>
        ))}
      </div>
      <div className="mt-4 max-w-[92%] rounded-2xl rounded-bl-md border border-(--schemes-border) bg-white px-3.5 py-3 text-sm leading-relaxed text-(--schemes-ink-soft)">
        {copy.assistant}
      </div>
      <button
        type="button"
        className="mt-2 inline-flex w-fit items-center gap-2 rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) px-3 py-1.5 text-xs font-semibold text-(--schemes-status-info-text)"
      >
        <span className="size-1.5 rounded-full bg-(--schemes-blue-400)" />
        {copy.found}
      </button>
    </TutorialFrame>
  );
}

function MiniSchemeCard({ scheme }: { scheme: PreviewScheme }) {
  return (
    <div className={cn(productCard, "flex min-h-36 flex-col p-3")}>
      <div className="mb-2 flex items-start gap-3">
        <SchemeLogo agency={scheme.agency} image={scheme.image} />
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

function ResultsPreview({ copy }: { copy: TutorialCopy }) {
  const [filter, setFilter] = useState<"all" | "msf" | "health">("all");
  const previewSchemes: PreviewScheme[] = copy.previewSchemes.map(
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
    { id: "all" as const, label: copy.filterAll, icon: Search },
    { id: "msf" as const, label: copy.filterAgency, icon: Building2 },
    { id: "health" as const, label: copy.filterHealthcare, icon: HeartPulse },
  ];

  return (
    <TutorialFrame className="p-0">
      <div className="border-b border-(--schemes-border) bg-white px-3 py-3">
        <p className="text-sm font-semibold text-(--schemes-blue-600)">
          {copy.found}
        </p>
        <p className="mt-0.5 text-xs text-(--schemes-muted)">{copy.filters}</p>
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

function DetailPreview({ copy }: { copy: TutorialCopy }) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <TutorialFrame className="p-0">
      <div className="border-b border-(--schemes-border-neutral) bg-white p-4">
        <div className="flex items-center gap-3">
          <SchemeLogo
            agency={copy.detailAgency}
            image="/landing/logos/msf.jpg"
            size="lg"
          />
          <div className="min-w-0">
            <p className="text-[11px] font-semibold text-(--schemes-muted)">
              {copy.detailAgency}
            </p>
            <h4 className="mt-1 font-(--font-head) text-lg font-semibold leading-tight text-(--schemes-blue-900)">
              {copy.detailScheme}
            </h4>
            <div className="mt-2">
              <span
                className={getSchemeCategoryChipClassName(
                  "Financial Assistance",
                  "px-2 py-0.5 text-[10px] font-semibold",
                )}
              >
                {copy.detailCategoryLabel}
              </span>
            </div>
          </div>
        </div>
        <div className="no-scrollbar mt-4 flex gap-1 overflow-x-auto rounded-xl border border-(--schemes-border) bg-(--schemes-blue-50) p-1">
          {copy.detailTabs.map((tab, index) => (
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
            {copy.overview}
          </p>
        )}
        {activeTab === 1 && (
          <div className="space-y-2">
            {copy.qualifies.map((item) => (
              <BulletItem key={item}>{item}</BulletItem>
            ))}
          </div>
        )}
        {activeTab === 2 && (
          <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
            {copy.apply}
          </p>
        )}
        {activeTab === 3 && (
          <div className="space-y-5">
            <div>
              <SectionLabel>{copy.serviceArea}</SectionLabel>
              <p className="text-sm leading-relaxed text-(--schemes-ink-soft)">
                {copy.serviceAreaValue}
              </p>
            </div>
            <div>
              <SectionLabel>{copy.contacts}</SectionLabel>
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  {
                    area: copy.branchCentral,
                    address: copy.centralAddress,
                  },
                  {
                    area: copy.branchWest,
                    address: copy.westAddress,
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
                      {copy.phone}
                    </div>
                    <div className="flex items-center gap-2 break-all text-(--schemes-blue-600)">
                      <Mail size={15} strokeWidth={2} className="shrink-0" />
                      {copy.email}
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
            {copy.share}
          </div>
          <div
            aria-hidden="true"
            className={`${productButtonSolidAmber} ${productButtonProminent} pointer-events-none relative w-full`}
          >
            <ExternalLink size={14} strokeWidth={2} className="shrink-0" />
            {copy.visit}
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
  stepLabel,
}: {
  step: number;
  title: string;
  description: string;
  preview: React.ReactNode;
  reverse?: boolean;
  stepLabel: string;
}) {
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
          <span className="sr-only">{stepLabel} </span>
          {step}
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
  const { t } = useLanguage();
  const copy = {
    ...t.features.tutorial,
    submitExampleQuery: t.a11y.submitExampleQuery,
  };

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
          {t.features.heading}
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground">
          {t.features.subtitle}
        </p>
      </motion.div>

      <div className="mx-auto mt-12 max-w-5xl md:mt-16 flex flex-col gap-20 md:gap-24">
        <WalkthroughRow
          step={1}
          stepLabel={copy.step}
          title={t.features.cards.search.title}
          description={t.features.cards.search.description}
          preview={
            <ComposerPreview
              copy={copy}
              placeholder={t.hero.searchPlaceholder}
            />
          }
        />
        <WalkthroughRow
          step={2}
          stepLabel={copy.step}
          title={t.features.cards.database.title}
          description={t.features.cards.database.description}
          preview={<SearchProgressPreview copy={copy} />}
          reverse
        />
        <WalkthroughRow
          step={3}
          stepLabel={copy.step}
          title={t.features.cards.filter.title}
          description={t.features.cards.filter.description}
          preview={<ResultsPreview copy={copy} />}
        />
        <WalkthroughRow
          step={4}
          stepLabel={copy.step}
          title={t.howItWorks.steps[2].title}
          description={t.howItWorks.steps[2].description}
          preview={<DetailPreview copy={copy} />}
          reverse
        />
      </div>
    </SectionWrapper>
  );
}
