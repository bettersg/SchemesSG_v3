import { SearchResScheme } from "@/types/types";
import { Spinner } from "@heroui/react";
import SchemeLogo from "./scheme-logo";
import Link from "next/link";

function Tag({ label, index }: { label: string; index: number }) {
  const palettes = [
	"bg-[#E6F1FB] text-[#185FA5] border-[#B5D4F4]",
	"bg-[#FAEEDA] text-[#BA7517] border-[#FAC775]",
	"bg-[#EEEDFE] text-[#534AB7] border-[#CECBF6]",
	"bg-[#EAF3DE] text-[#3B6D11] border-[#C0DD97]",
  ];
  return (
	<span
	  className={`inline-flex text-[11px] font-medium px-2.5 py-0.5 rounded-full border ${palettes[index % palettes.length]}`}
	>
	  {label.trim()}
	</span>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
	<div className="flex gap-2.5 items-start text-sm text-[#444441]">
	  <div className="w-[18px] h-[18px] rounded-[5px] bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center shrink-0 mt-0.5">
		<svg width="9" height="9" viewBox="0 0 10 10" fill="none">
		  <path
			d="M2 5l2.5 2.5 4-4"
			stroke="#185FA5"
			strokeWidth="1.5"
			strokeLinecap="round"
			strokeLinejoin="round"
		  />
		</svg>
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
	<div className="flex items-center gap-2 mb-3">
	  <div className={`w-2 h-2 rounded-[3px] ${color}`} />
	  <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#B4B2A9]">
		{children}
	  </span>
	</div>
  );
}

export default function SchemeContent({
  scheme,
//   onClose,
}: {
  scheme: SearchResScheme | null;
//   onClose: () => void;
}) {
  if (!scheme) return null;

  const types = scheme.schemeType;
  const targetItems = scheme.targetAudience;
  const benefitItems = scheme.benefits;

  return (
    <>
      {/* ── Hero header ── */}
      <div className="bg-[#E6F1FB] border-b border-[#e0eef8] px-5 py-5 relative">
        <div className="flex gap-3 items-start pr-8">
          <SchemeLogo agency={scheme.agency} image={scheme.image} />
          <div className="flex-1 min-w-0">
            <h1 className="font-[var(--font-head)] text-[17px] font-bold text-[#042C53] leading-snug mb-1">
              {scheme.schemeName}
            </h1>
            <p className="text-xs text-[#B4B2A9] mb-2.5">{scheme.agency}</p>
            {types && (
              <div className="flex gap-1.5 flex-wrap">
                {types.map((t, i) => (
                  <Tag key={t} label={t} index={i} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Scrollable body ── */}
      <div className="flex-1 divide-y divide-[#f0f4f8] overflow-y-auto thin-scrollbar p-0">
        {scheme.description && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#378ADD]">About</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed whitespace-pre-wrap">
              {scheme.description}
            </p>
          </div>
        )}
        {targetItems && targetItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#EF9F27]">Who qualifies</SectionLabel>
            <div className="flex flex-col gap-2">
              {targetItems.map((t) => (
                <CheckItem key={t} text={t} />
              ))}
            </div>
          </div>
        )}
        {benefitItems && benefitItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#1D9E75]">What you receive</SectionLabel>
            <div className="flex flex-col gap-2">
              {benefitItems.map((b) => (
                <CheckItem key={b} text={b} />
              ))}
            </div>
          </div>
        )}
        {scheme.eligibilityText && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#7F77DD]">Eligibility</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed">
              {scheme.eligibilityText}
            </p>
          </div>
        )}
        {scheme.howToApply && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#534AB7]">How to apply</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed">
              {scheme.howToApply}
            </p>
          </div>
        )}
        {scheme.contact && scheme.contact.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#B4B2A9]">Contact</SectionLabel>
            <div className="flex flex-col gap-2.5">
              {scheme.contact.map((c, i) => (
                <div
                  key={i}
                  className="text-sm text-[#5F5E5A] flex flex-col gap-1.5"
                >
                  {c.planningArea && (
                    <p className="font-semibold text-[#042C53] text-xs uppercase tracking-wide">
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
                      <span className="text-base">📍</span> {c.address}
                    </a>
                  )}
                  {c.phones?.map((p) => (
                    <a
                      key={p}
                      href={`tel:${p}`}
                      className="flex items-center gap-2 text-[#185FA5] hover:underline"
                    >
                      <span className="text-base">📞</span> {p}
                    </a>
                  ))}
                  {c.emails?.map((e) => (
                    <a
                      key={e}
                      href={`mailto:${e}`}
                      className="flex items-center gap-2 text-[#185FA5] hover:underline break-all"
                    >
                      <span className="text-base">✉️</span> {e}
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Footer CTAs ── */}
      <div className="border-t border-[#e8eef6] flex flex-col gap-2.5 px-5 py-4">
        {scheme.link && (
          <Link
            href={scheme.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-[#185FA5] text-white text-sm font-semibold hover:bg-[#0C447C] transition-colors"
          >
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <path
                d="M12 7H2M8 3l4 4-4 4"
                stroke="white"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Visit agency website
          </Link>
        )}
        <Link
          href={`/schemes/${scheme.schemeId}`}
          target="_blank"
          className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-transparent border-[1.5px] border-[#B5D4F4] text-[#185FA5] text-sm font-semibold hover:bg-[#E6F1FB] transition-colors"
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path
              d="M5 2H2v10h10V9M8 2h4v4M8 6l4-4"
              stroke="#185FA5"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          View full scheme page
        </Link>
        <p className="text-center text-[10.5px] text-[#B4B2A9] flex items-center justify-center gap-1">
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
            <path
              d="M9 1.5L10.5 3 6 7.5l-3 1 1-3L9 1.5Z"
              stroke="#B4B2A9"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          </svg>
          Share
          <span className="mx-1">·</span>
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 4h8M2 4l3-3M2 4l3 3"
              stroke="#B4B2A9"
              strokeWidth="1.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Copy link
        </p>
      </div>
    </>
  );
}