"use client";
import { useEffect, useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { parseArrayString } from "@/lib/utils";
import { BranchContact } from "@/types/types";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { Spinner } from "@heroui/react";

interface DrawerScheme {
  schemeId: string;
  schemeName: string;
  agency: string;
  schemeType?: string[];
  description?: string;
  targetAudience?: string[];
  benefits?: string[];
  eligibilityText?: string;
  howToApply?: string;
  link?: string;
  contact?: BranchContact[];
}

interface SchemeDrawerProps {
  schemeId: string | null;
  onClose: () => void;
}

function Tag({ label, index }: { label: string; index: number }) {
  const palettes = [
    "bg-[#E6F1FB] text-[#185FA5] border-[#B5D4F4]",
    "bg-[#FAEEDA] text-[#BA7517] border-[#FAC775]",
    "bg-[#EEEDFE] text-[#534AB7] border-[#CECBF6]",
    "bg-[#EAF3DE] text-[#3B6D11] border-[#C0DD97]",
  ];
  return (
    <span className={`inline-flex text-[11px] font-medium px-2.5 py-0.5 rounded-full border ${palettes[index % palettes.length]}`}>
      {label.trim()}
    </span>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex gap-2.5 items-start text-sm text-[#444441]">
      <div className="w-[18px] h-[18px] rounded-[5px] bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center shrink-0 mt-0.5">
        <svg width="9" height="9" viewBox="0 0 10 10" fill="none">
          <path d="M2 5l2.5 2.5 4-4" stroke="#185FA5" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <span className="leading-snug">{text.trim()}</span>
    </div>
  );
}

function SectionLabel({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className={`w-2 h-2 rounded-[3px] ${color}`} />
      <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#B4B2A9]">{children}</span>
    </div>
  );
}

export default function SchemeDrawer({ schemeId, onClose }: SchemeDrawerProps) {
  const [scheme, setScheme] = useState<DrawerScheme | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!schemeId) { setScheme(null); return; };
    setIsLoading(true);
    setScheme(null);
    fetchWithAuth(`${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes/${schemeId}`)
      .then((r) => r.json())
      .then((res) => {
        const d = res.data;
        if (!d) return;
        const contacts: BranchContact[] = [];
        const areas = parseArrayString(d.planning_area);
        const phones = parseArrayString(d.phone);
        const emails = parseArrayString(d.email);
        const addresses = parseArrayString(d.address);
        if (areas && areas.length > 0) {
          areas.forEach((area: string, i: number) => {
            contacts.push({
              planningArea: area,
              phones: phones ? [phones[Math.min(i, phones.length - 1)]] : undefined,
              emails: emails ? [emails[Math.min(i, emails.length - 1)]] : undefined,
              address: addresses ? addresses[i] : undefined,
            });
          });
        } else if (phones || emails) {
          contacts.push({ phones: phones || undefined, emails: emails || undefined });
        }
        setScheme({
          schemeId,
          schemeName: d.scheme || "",
          agency: d.agency || "",
          schemeType: d.scheme_type || "",
          description: d.llm_description || d.description || "",
          targetAudience: d.who_is_it_for || "",
          benefits: d.what_it_gives || "",
          eligibilityText: d.eligibility || "",
          howToApply: d.how_to_apply || "",
          link: d.link || "",
          contact: contacts,
        });
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [schemeId]);

  const types        = scheme?.schemeType;
  const targetItems  = scheme?.targetAudience;
  const benefitItems = scheme?.benefits;
  const agencyInitials = scheme
    ? scheme.agency.split(" ").slice(0, 2).map((w) => w[0]).join("").toUpperCase()
    : "";

  return (
    <AnimatePresence>
      {schemeId && (
        <>
          {/* ── DESKTOP: backdrop dims ONLY the chat column, drawer slides from LEFT ── */}
          {/* The backdrop is position:absolute inside the chat-main column (see chat-page),
              so the right scheme-list-panel is unaffected. */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="absolute inset-0 bg-[#042C53]/30 backdrop-blur-[1.5px] z-20 hidden lg:block"
            onClick={onClose}
          />

          {/* ── DESKTOP: left-side panel ── */}
          <motion.div
            initial={{ x: "-100%" }} animate={{ x: 0 }} exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 340, damping: 34 }}
            className="absolute top-0 left-0 bottom-0 w-[380px] lg:w-full bg-white z-30 shadow-[8px_0_40px_rgba(0,0,0,0.13)] overflow-y-auto thin-scrollbar hidden lg:flex flex-col"
          >
            <DrawerContent
              scheme={scheme} isLoading={isLoading} onClose={onClose}
              types={types} targetItems={targetItems} benefitItems={benefitItems}
              agencyInitials={agencyInitials}
            />
          </motion.div>

          {/* ── MOBILE: full-screen backdrop ── */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="fixed inset-0 bg-[#042C53]/35 backdrop-blur-[2px] z-40 lg:hidden"
            onClick={onClose}
          />

          {/* ── MOBILE: bottom sheet ── */}
          <motion.div
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="fixed left-0 right-0 bottom-0 h-[88vh] bg-white z-50 rounded-t-[20px] shadow-[0_-8px_40px_rgba(0,0,0,0.15)] overflow-y-auto thin-scrollbar flex flex-col lg:hidden"
          >
            <div className="bg-[#E6F1FB]">
				<div className="w-9 h-1 rounded-full bg-[#D3D1C7] mx-auto mt-3 shrink-0" />
			</div>
            <DrawerContent
              scheme={scheme} isLoading={isLoading} onClose={onClose}
              types={types} targetItems={targetItems} benefitItems={benefitItems}
              agencyInitials={agencyInitials}
            />
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function DrawerContent({
  scheme, isLoading, onClose, types, targetItems, benefitItems, agencyInitials,
}: {
  scheme: DrawerScheme | null;
  isLoading: boolean;
  onClose: () => void;
  types: string[] | undefined;
  targetItems: string[] | undefined;
  benefitItems: string[] | undefined;
  agencyInitials: string;
}) {
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }
  if (!scheme) return null;

  return (
    <div className="flex flex-col flex-1">
      {/* Hero */}
      <div className="bg-[#E6F1FB] px-5 py-5 border-b border-[#e0eef8] relative shrink-0">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/6 hover:bg-black/10 flex items-center justify-center text-[#5F5E5A] transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </button>
        <div className="flex gap-3 items-start pr-8">
          <div className="w-14 h-14 rounded-[14px] bg-[#185FA5] flex items-center justify-center text-white font-bold text-base shrink-0 border-2 border-white/60">
            {agencyInitials}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-[var(--font-head)] text-[17px] font-bold text-[#042C53] leading-snug mb-1">
              {scheme.schemeName}
            </h2>
            <p className="text-xs text-[#B4B2A9] mb-2.5">{scheme.agency}</p>
            {types && <div className="flex gap-1.5 flex-wrap">
              {types.map((t, i) => <Tag key={t} label={t} index={i} />)}
            </div>}
          </div>
        </div>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 divide-y divide-[#f0f4f8] overflow-y-auto thin-scrollbar">
        {scheme.description && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#378ADD]">About</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed whitespace-pre-wrap">{scheme.description}</p>
          </div>
        )}
        {targetItems && targetItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#EF9F27]">Who qualifies</SectionLabel>
            <div className="flex flex-col gap-2">
              {targetItems.map((t) => <CheckItem key={t} text={t} />)}
            </div>
          </div>
        )}
        {benefitItems && benefitItems.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#1D9E75]">What you receive</SectionLabel>
            <div className="flex flex-col gap-2">
              {benefitItems.map((b) => <CheckItem key={b} text={b} />)}
            </div>
          </div>
        )}
        {scheme.eligibilityText && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#7F77DD]">Eligibility</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed">{scheme.eligibilityText}</p>
          </div>
        )}
        {scheme.howToApply && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#534AB7]">How to apply</SectionLabel>
            <p className="text-sm text-[#5F5E5A] leading-relaxed">{scheme.howToApply}</p>
          </div>
        )}
        {scheme.contact && scheme.contact.length > 0 && (
          <div className="px-5 py-4">
            <SectionLabel color="bg-[#B4B2A9]">Contact</SectionLabel>
            <div className="flex flex-col gap-2.5">
              {scheme.contact.map((c, i) => (
                <div key={i} className="text-sm text-[#5F5E5A] flex flex-col gap-1.5">
                  {c.planningArea && (
                    <p className="font-semibold text-[#042C53] text-xs uppercase tracking-wide">{c.planningArea}</p>
                  )}
                  {c.address && (
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(c.address)}`}
                      target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-[#5F5E5A] hover:text-[#185FA5]"
                    >
                      <span className="text-base">📍</span> {c.address}
                    </a>
                  )}
                  {c.phones?.map((p) => (
                    <a key={p} href={`tel:${p}`} className="flex items-center gap-2 text-[#185FA5] hover:underline">
                      <span className="text-base">📞</span> {p}
                    </a>
                  ))}
                  {c.emails?.map((e) => (
                    <a key={e} href={`mailto:${e}`} className="flex items-center gap-2 text-[#185FA5] hover:underline break-all">
                      <span className="text-base">✉️</span> {e}
                    </a>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* CTAs */}
      <div className="px-5 py-4 border-t border-[#e8eef6] flex flex-col gap-2.5 shrink-0">
        {scheme.link && (
          <Link
            href={scheme.link} target="_blank" rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-[#185FA5] text-white text-sm font-semibold hover:bg-[#0C447C] transition-colors"
          >
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <path d="M12 7H2M8 3l4 4-4 4" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Visit agency website
          </Link>
        )}
        <Link
          href={`/schemes/${scheme.schemeId}`} target="_blank"
          className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-transparent border-[1.5px] border-[#B5D4F4] text-[#185FA5] text-sm font-semibold hover:bg-[#E6F1FB] transition-colors"
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M5 2H2v10h10V9M8 2h4v4M8 6l4-4" stroke="#185FA5" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          View full scheme page
        </Link>
        <p className="text-center text-[10.5px] text-[#B4B2A9] flex items-center justify-center gap-1">
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
            <path d="M9 1.5L10.5 3 6 7.5l-3 1 1-3L9 1.5Z" stroke="#B4B2A9" strokeWidth="1.2" strokeLinejoin="round"/>
          </svg>
          Share
          <span className="mx-1">·</span>
          <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
            <path d="M2 4h8M2 4l3-3M2 4l3 3" stroke="#B4B2A9" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Copy link
        </p>
      </div>
    </div>
  );
}
