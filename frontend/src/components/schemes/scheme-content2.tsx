import { Scheme } from "@/types/types";
import SchemeLogo from "./scheme-logo";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  ExternalLink,
  Mail,
  MapPin,
  Phone,
} from "lucide-react";
import {
  getSchemeCategoryChipClassName,
  normalizeSchemeCategory,
} from "@/lib/design-system/categories";

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
    <div className="flex items-start gap-2.5 text-sm text-[#444441]">
      <div className="mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[5px] border border-[#B5D4F4] bg-[#E6F1FB]">
        <Check size={9} strokeWidth={2} className="text-[#185FA5]" />
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
      <span className="text-[10px] font-semibold tracking-[0.08em] text-[#B4B2A9] uppercase">
        {children}
      </span>
    </div>
  );
}

export default function SchemeContent2({ scheme }: { scheme: Scheme | null }) {
  if (!scheme) return null;

  const types = scheme.schemeType;
  const targetItems = scheme.targetAudience;
  const benefitItems = scheme.benefits;

  return (
    <div className="min-h-full w-full overflow-y-auto bg-[#FAFBFD] p-4 sm:p-8">
      <div className="mx-auto max-w-5xl">
        {/* ── Title section ── */}
        <div className="mb-8 flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:text-left">
          <SchemeLogo agency={scheme.agency} image={scheme.image} />
          <div className="flex flex-col items-center gap-2 sm:items-start">
            {scheme.agency && (
              <h1 className="text-2xl font-semibold text-[#042C53] sm:text-3xl">
                {scheme.agency}
              </h1>
            )}
            {scheme.schemeName && (
              <p className="text-base text-[#5F5E5A]">{scheme.schemeName}</p>
            )}
            {scheme.link && (
              <Link
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm font-semibold text-[#185FA5] transition-colors hover:text-[#0C447C]"
              >
                Find out more
                <ExternalLink size={13} strokeWidth={1.7} />
              </Link>
            )}
          </div>
        </div>

        {/* ── Description card ── */}
        {scheme.description && (
          <div className="mb-6 rounded-2xl border border-[#e0eef8] bg-white p-6">
            <SectionLabel color="bg-[#378ADD]">About</SectionLabel>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#5F5E5A]">
              {scheme.description}
            </p>
          </div>
        )}

        {/* ── Details card ── */}
        <div className="mb-6 rounded-2xl border border-[#e0eef8] bg-white p-6">
          <div className="mb-5 flex items-center gap-2">
            <span className="text-lg font-semibold text-[#042C53]">
              Details
            </span>
          </div>

          <div className="flex flex-col gap-8 lg:flex-row">
            {/* Left column — main details */}
            <div className="flex flex-[2] flex-col gap-6">
              {/* Who qualifies & What you receive — side by side on sm+ */}
              <div className="flex flex-col gap-6 sm:flex-row">
                {targetItems && targetItems.length > 0 && (
                  <div className="flex-1">
                    <SectionLabel color="bg-[#EF9F27]">
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
                  <div className="flex-1">
                    <SectionLabel color="bg-[#378ADD]">
                      What you receive
                    </SectionLabel>
                    <div className="flex flex-col gap-2">
                      {benefitItems.map((b) => (
                        <CheckItem key={b} text={b} />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Eligibility */}
              {scheme.eligibilityText && (
                <div>
                  <SectionLabel color="bg-[#378ADD]">Eligibility</SectionLabel>
                  <p className="text-sm leading-relaxed text-[#5F5E5A]">
                    {scheme.eligibilityText}
                  </p>
                </div>
              )}

              {/* How to apply */}
              {scheme.howToApply && (
                <div>
                  <SectionLabel color="bg-[#378ADD]">How to apply</SectionLabel>
                  <p className="text-sm leading-relaxed text-[#5F5E5A]">
                    {scheme.howToApply}
                  </p>
                </div>
              )}
            </div>

            {/* Right column — metadata */}
            <div className="flex flex-1 flex-col gap-6">
              {/* Type tags */}
              {types && types.length > 0 && (
                <div>
                  <SectionLabel color="bg-[#378ADD]">Type</SectionLabel>
                  <div className="flex flex-wrap gap-1.5">
                    {types.map((t) => (
                      <Tag key={t} label={t} />
                    ))}
                  </div>
                </div>
              )}

              {/* Service area */}
              {scheme.serviceArea && (
                <div>
                  <SectionLabel color="bg-[#B4B2A9]">Service area</SectionLabel>
                  <p className="text-sm text-[#5F5E5A]">{scheme.serviceArea}</p>
                </div>
              )}

              {/* Contact */}
              {scheme.contact && scheme.contact.length > 0 && (
                <div>
                  <SectionLabel color="bg-[#B4B2A9]">Contact</SectionLabel>
                  <div className="flex flex-col gap-3">
                    {scheme.contact.map((c, i) => (
                      <div
                        key={i}
                        className="flex flex-col gap-1.5 rounded-xl border border-[#e0eef8] bg-[#FAFBFD] p-3.5 text-sm text-[#5F5E5A]"
                      >
                        {c.planningArea && (
                          <p className="text-xs font-semibold tracking-wide text-[#042C53] uppercase">
                            {c.planningArea}
                          </p>
                        )}
                        {c.address && (
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.address)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 text-[#5F5E5A] hover:text-[#185FA5]"
                          >
                            <MapPin
                              size={16}
                              strokeWidth={2}
                              className="shrink-0"
                            />{" "}
                            {c.address}
                          </a>
                        )}
                        {c.phones?.map((p) => (
                          <a
                            key={p}
                            href={`tel:${p}`}
                            className="flex items-center gap-2 text-[#185FA5] hover:underline"
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
                            className="flex items-center gap-2 break-all text-[#185FA5] hover:underline"
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

          {/* CTA inside details card */}
          {scheme.link && (
            <div className="mt-8 flex flex-wrap justify-center gap-3 border-t border-[#e0eef8] pt-5 sm:justify-end">
              <Link
                href={scheme.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-(--schemes-amber-400) px-6 py-3 text-sm font-semibold text-(--schemes-ink) transition-colors hover:bg-(--schemes-amber-100)"
              >
                <ArrowRight size={13} strokeWidth={2} />
                Visit agency website
              </Link>
            </div>
          )}
        </div>

        {/* ── Disclaimer ── */}
        <section className="mb-8 rounded-2xl border border-[#e0eef8] bg-white p-4">
          <div className="flex items-start gap-3">
            <div className="text-[#B4B2A9] text-lg">ⓘ</div>
            <div>
              <h3 className="mb-1 text-sm font-semibold text-[#042C53]">
                Important Information
              </h3>
              <p className="text-sm text-[#5F5E5A]">
                We strive to provide accurate information about assistance
                schemes in Singapore. Program details may change over time, so
                please visit the official website for the most current
                information.{" "}
                <Link
                  href="/feedback"
                  className="text-sm text-[#185FA5] hover:underline"
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
