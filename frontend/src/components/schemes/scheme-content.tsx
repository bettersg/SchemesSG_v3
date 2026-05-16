import { Scheme } from "@/types/types";
import SchemeLogo from "./scheme-logo";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ExternalLink,
  Mail,
  MapPin,
  Pencil,
  Phone,
} from "lucide-react";
import {
  getSchemeCategoryChipClassName,
  normalizeSchemeCategory,
} from "@/lib/design-system/categories";
import {
  productButtonLg,
  productButtonPrimary,
  productButtonSecondary,
} from "@/lib/design-system/product-styles";

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

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2.5 text-sm text-(--schemes-ink-soft)">
      <div className="mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[5px] border border-(--schemes-blue-100) bg-(--schemes-blue-50)">
        <Check
          size={9}
          strokeWidth={2}
          className="text-(--schemes-blue-600)"
        />
      </div>
      <span className="leading-snug">{text.trim()}</span>
    </div>
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

export default function SchemeContent({
  scheme,
  //   onClose,
}: {
  scheme: Scheme | null;
  //   onClose: () => void;
}) {
  if (!scheme) return null;

  const types = scheme.schemeType;
  const targetItems = scheme.targetAudience;
  const benefitItems = scheme.benefits;

  return (
    <>
      {/* ── Hero header ── */}
      <div className="relative border-b border-(--schemes-border) bg-(--schemes-blue-50) px-5 py-5">
        <div className="flex items-start gap-3 pr-8">
          <SchemeLogo agency={scheme.agency} image={scheme.image} />
          <div className="min-w-0 flex-1">
            <h1 className="mb-1 text-[17px] leading-snug font-semibold text-(--schemes-blue-900)">
              {scheme.schemeName}
            </h1>
            <p className="mb-2.5 text-xs text-(--schemes-muted)">
              {scheme.agency}
            </p>
            {types && (
              <div className="flex flex-wrap gap-1.5">
                {types.map((t) => (
                  <Tag key={t} label={t} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Scrollable body ── */}
      <div className="thin-scrollbar flex-1 divide-y divide-(--schemes-border) overflow-y-auto p-0">
        {scheme.description && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-blue-400)">
              About
            </SectionLabel>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-(--schemes-muted)">
              {scheme.description}
            </p>
          </div>
        )}
        {targetItems && targetItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-amber-400)">
              Who qualifies
            </SectionLabel>
            <div className="flex flex-col gap-2">
              {targetItems.map((t) => (
                <CheckItem key={t} text={t} />
              ))}
            </div>
          </div>
        )}
        {benefitItems && benefitItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-blue-400)">
              What you receive
            </SectionLabel>
            <div className="flex flex-col gap-2">
              {benefitItems.map((b) => (
                <CheckItem key={b} text={b} />
              ))}
            </div>
          </div>
        )}
        {scheme.eligibilityText && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-blue-400)">
              Eligibility
            </SectionLabel>
            <p className="text-sm leading-relaxed text-(--schemes-muted)">
              {scheme.eligibilityText}
            </p>
          </div>
        )}
        {scheme.howToApply && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-blue-400)">
              How to apply
            </SectionLabel>
            <p className="text-sm leading-relaxed text-(--schemes-muted)">
              {scheme.howToApply}
            </p>
          </div>
        )}
        {scheme.contact && scheme.contact.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-(--schemes-muted-light)">
              Contact
            </SectionLabel>
            <div className="flex flex-col gap-2.5">
              {scheme.contact.map((c, i) => (
                <div
                  key={i}
                  className="flex flex-col gap-1.5 text-sm text-(--schemes-muted)"
                >
                  {c.planningArea && (
                    <p className="text-xs font-semibold tracking-wide text-(--schemes-blue-900) uppercase">
                      {c.planningArea}
                    </p>
                  )}
                  {c.address && (
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.address)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-(--schemes-muted) hover:text-(--schemes-blue-600)"
                    >
                      <MapPin size={16} strokeWidth={2} className="shrink-0" />{" "}
                      {c.address}
                    </a>
                  )}
                  {c.phones?.map((p) => (
                    <a
                      key={p}
                      href={`tel:${p}`}
                      className="flex items-center gap-2 text-(--schemes-blue-600) hover:underline"
                    >
                      <Phone size={16} strokeWidth={2} className="shrink-0" />{" "}
                      {p}
                    </a>
                  ))}
                  {c.emails?.map((e) => (
                    <a
                      key={e}
                      href={`mailto:${e}`}
                      className="flex items-center gap-2 break-all text-(--schemes-blue-600) hover:underline"
                    >
                      <Mail size={16} strokeWidth={2} className="shrink-0" />{" "}
                      {e}
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Footer CTAs ── */}
      <div className="flex flex-col gap-2.5 border-t border-(--schemes-border) px-5 py-4">
        {scheme.link && (
          <Link
            href={scheme.link}
            target="_blank"
            rel="noopener noreferrer"
            className={`${productButtonPrimary} ${productButtonLg} w-full`}
          >
            <ArrowRight size={13} strokeWidth={2} />
            Visit agency website
          </Link>
        )}
        <Link
          href={`/schemes/${scheme.schemeId}`}
          target="_blank"
          className={`${productButtonSecondary} ${productButtonLg} w-full`}
        >
          <ExternalLink size={13} strokeWidth={1.7} />
          View full scheme page
        </Link>
        <p className="flex items-center justify-center gap-1 text-center text-[10.5px] text-(--schemes-muted)">
          <Pencil size={10} strokeWidth={1.6} />
          Share
          <span className="mx-1">·</span>
          <ArrowLeft size={10} strokeWidth={1.7} />
          Copy link
        </p>
      </div>
    </>
  );
}
