"use client";
import { fetchWithAuth } from "@/lib/api";
import { parseArrayString } from "@/lib/helper";
import { Spinner } from "@heroui/react";
import Markdown from "react-markdown";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "./scheme.module.css";

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

function SectionCard({ iconBg, iconContent, title, children }: {
  iconBg: string; iconContent: React.ReactNode; title: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-[#e4edf7] rounded-2xl px-6 py-5 shadow-[0_2px_12px_rgba(4,44,83,0.06)]">
      <div className="flex items-center gap-2.5 mb-4">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
          {iconContent}
        </div>
        <h3 className="font-[var(--font-head)] text-[14px] font-semibold text-[#042C53]">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function CheckItem({ text }: { text: string }) {
  return (
    <div className="flex gap-2.5 items-start text-sm text-[#444441]">
      <div className="w-5 h-5 rounded-[6px] bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center shrink-0 mt-0.5">
        <svg width="9" height="9" viewBox="0 0 10 10" fill="none">
          <path d="M2 5l2.5 2.5 4-4" stroke="#185FA5" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <span className="leading-snug">{text.trim()}</span>
    </div>
  );
}

function ApplyStep({ number, title, desc }: { number: number; title: string; desc: string }) {
  return (
    <div className="flex gap-3.5 pb-4 relative">
      {number < 3 && <div className="absolute left-[13px] top-7 bottom-0 w-[1.5px] bg-gradient-to-b from-[#B5D4F4] to-transparent" />}
      <div className="w-7 h-7 rounded-full bg-[#185FA5] text-white text-xs font-bold flex items-center justify-center shrink-0 font-[var(--font-head)] z-10">
        {number}
      </div>
      <div>
        <p className="text-sm font-semibold text-[#042C53] mb-0.5">{title}</p>
        <p className="text-xs text-[#5F5E5A] leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

export default function SchemePage() {
  const { schemeId } = useParams();
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchScheme() {
      if (!schemeId) { setError("Invalid schemeId"); setIsLoading(false); return; }
      try {
        const id = Array.isArray(schemeId) ? schemeId[0] : schemeId;
        const response = await fetchWithAuth(`${process.env.NEXT_PUBLIC_API_BASE_URL}/schemes/${id}`);
        if (!response.ok) throw new Error("Failed to fetch");
        const res = await response.json();
        const d = res.data as ApiSchemeData;
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
          schemeType: d.scheme_type || "", 
		  schemeName: d.scheme || "",
          targetAudience: d.who_is_it_for || "", 
		  agency: d.agency || "",
          description: d.llm_description || d.description || "",
          scrapedText: d.scraped_text || "", 
		  benefits: d.what_it_gives || "",
          link: d.link || "", 
		  image: d.image || "", 
		  searchBooster: d.search_booster || "",
          schemeId: id, 
		  query: "", 
		  similarity: 0, quintile: 0,
          planningArea: d.planning_area || "", 
		  summary: d.summary || "",
          contact: contacts, 
		  howToApply: d.how_to_apply || "",
          eligibilityText: d.eligibility || "", 
		  serviceArea: d.service_area || "",
          lastUpdated: d.last_modified_date ? new Date(d.last_modified_date).toLocaleDateString("en-SG") : "",
        });
      } catch { setError("An error occurred loading this scheme."); }
      finally { setIsLoading(false); }
    }
    fetchScheme();
  }, [schemeId]);

  if (isLoading) return (
    <div className="min-h-screen bg-[#f4f7fb] flex items-center justify-center">
      <Spinner size="lg" />
    </div>
  );
  if (error) return (
    <div className="min-h-screen bg-[#f4f7fb] flex items-center justify-center">
      <p className="text-[#E24B4A]">{error}</p>
    </div>
  );
  if (!scheme) return null;

  const types = scheme.schemeType.slice(0, 4);
  const targetItems = scheme.targetAudience;
  const benefitItems = scheme.benefits;
  const agencyInitials = scheme.agency.split(" ").slice(0, 2).map((w: string) => w[0]).join("").toUpperCase();

  return (
    <div className="min-h-screen bg-[#f4f7fb]">
      {/* Navbar supplement */}
      <div className="bg-white border-b border-[#e8eef6] px-4 sm:px-8 py-2">
        <div className="max-w-[720px] mx-auto flex items-center gap-2 text-xs text-[#B4B2A9]">
          <Link href="/" className="text-[#378ADD] hover:underline">Home</Link>
          <span>›</span>
          <Link href="/explore" className="text-[#378ADD] hover:underline">Explore</Link>
          <span>›</span>
          <span className="text-[#5F5E5A] truncate">{scheme.schemeName}</span>
        </div>
      </div>

      <div className="max-w-[720px] mx-auto px-4 sm:px-6 py-7 pb-16">
        {/* Hero card */}
        <div className="bg-white border border-[#e4edf7] rounded-2xl overflow-hidden mb-5 shadow-[0_2px_12px_rgba(4,44,83,0.06)]">
          <div className="bg-gradient-to-br from-[#042C53] to-[#185FA5] px-6 pt-6 pb-5 relative overflow-hidden">
            <div className="absolute top-[-40px] right-[-40px] w-32 h-32 rounded-full bg-white/5" />
            <div className="absolute bottom-[-30px] left-1/3 w-48 h-28 rounded-full bg-white/3" />
            <div className="flex gap-4 items-start relative z-10">
              <div className="w-14 h-14 rounded-[14px] bg-white/15 border-2 border-white/30 flex items-center justify-center text-white font-bold text-base shrink-0 font-[var(--font-head)] backdrop-blur-sm">
                {agencyInitials}
              </div>
              <div className="flex-1 min-w-0">
                <h1 className="font-[var(--font-head)] text-xl font-bold text-white leading-snug mb-1">{scheme.schemeName}</h1>
                <p className="text-sm text-white/70 mb-3">{scheme.agency}</p>
                <div className="flex gap-1.5 flex-wrap">
                  {types.map((t, i) => (
                    <span key={t} className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-white/15 border border-white/25 text-white/90">
                      {t.trim()}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                <button className="flex items-center gap-1.5 bg-white/12 border border-white/20 rounded-full px-3 py-1 text-[10.5px] text-white/85 hover:bg-white/20 transition-colors">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none"><path d="M9 1.5L10.5 3 6 7.5l-3 1 1-3L9 1.5Z" stroke="rgba(255,255,255,.85)" strokeWidth="1.2" strokeLinejoin="round"/></svg>
                  Share
                </button>
                <button className="flex items-center gap-1.5 bg-white/12 border border-white/20 rounded-full px-3 py-1 text-[10.5px] text-white/85 hover:bg-white/20 transition-colors">
                  <svg width="10" height="10" viewBox="0 0 12 12" fill="none"><path d="M2 4h8M2 4l3-3M2 4l3 3" stroke="rgba(255,255,255,.85)" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  Copy link
                </button>
              </div>
            </div>
          </div>
          <div className="px-6 py-5">
            {scheme.description && (
              <div className={`text-sm text-[#5F5E5A] leading-relaxed mb-5 ${styles.showMarker}`}>
                <Markdown>{scheme.description}</Markdown>
              </div>
            )}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Target group", value: scheme.targetAudience ? scheme.targetAudience : "Open to all" },
                { label: "Income criteria", value: "Open to all" },
                { label: "How to access", value: "Walk-in / Referral" },
              ].map((f) => (
                <div key={f.label} className="bg-[#f7fafd] border border-[#e4edf7] rounded-lg px-3 py-2.5">
                  <p className="text-[9px] font-bold uppercase tracking-[0.07em] text-[#B4B2A9] mb-1">{f.label}</p>
                  <p className="text-xs font-semibold text-[#0C447C] leading-snug">{f.value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Apply CTA card */}
        <div className="bg-white border-[1.5px] border-[#B5D4F4] rounded-2xl px-6 py-5 mb-5 shadow-[0_2px_8px_rgba(24,95,165,0.06)]">
          <h3 className="font-[var(--font-head)] text-[15px] font-bold text-[#042C53] mb-1">Ready to access this scheme?</h3>
          <p className="text-xs text-[#5F5E5A] mb-4">Contact {scheme.agency} to book your intake appointment.</p>
          <div className="grid grid-cols-2 gap-2.5 mb-3">
            {scheme.link && (
              <Link href={scheme.link} target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#185FA5] text-white text-xs font-semibold hover:bg-[#0C447C] transition-colors">
                <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M12 7H2M8 3l4 4-4 4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                Visit website
              </Link>
            )}
            {scheme.contact?.[0]?.phones?.[0] && (
              <a href={`tel:${scheme.contact[0].phones[0]}`}
                className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-transparent border-[1.5px] border-[#B5D4F4] text-[#185FA5] text-xs font-semibold hover:bg-[#E6F1FB] transition-colors">
                <svg width="12" height="12" viewBox="0 0 14 14" fill="none"><path d="M3 7a4 4 0 108 0 4 4 0 00-8 0zm4-2v2l1.5 1.5" stroke="#185FA5" strokeWidth="1.3" strokeLinecap="round"/></svg>
                Call {scheme.contact[0].phones[0]}
              </a>
            )}
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 rounded-lg bg-[#F1EFE8] border border-[#D3D1C7] text-xs font-medium text-[#5F5E5A] hover:bg-[#e8e5dc] transition-colors flex items-center justify-center gap-1.5">
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none"><path d="M9 1.5L10.5 3 6 7.5l-3 1 1-3L9 1.5Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/></svg>Share
            </button>
            <button className="flex-1 py-2 rounded-lg bg-[#F1EFE8] border border-[#D3D1C7] text-xs font-medium text-[#5F5E5A] hover:bg-[#e8e5dc] transition-colors flex items-center justify-center gap-1.5">
              <svg width="10" height="10" viewBox="0 0 12 12" fill="none"><path d="M2 4h8M2 4l3-3M2 4l3 3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>Copy link
            </button>
          </div>
        </div>

        {/* Who qualifies */}
        {targetItems.length > 0 && (
          <SectionCard
            iconBg="bg-[#FAEEDA]"
            iconContent={<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M8 2L14 5V11L8 14L2 11V5L8 2Z" stroke="#BA7517" strokeWidth="1.4"/><path d="M5 8l2 2 4-4" stroke="#BA7517" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            title="Who qualifies"
          >
            <div className="flex flex-col gap-2">
              {targetItems.map(t => <CheckItem key={t} text={t} />)}
            </div>
          </SectionCard>
        )}

        {/* What you receive */}
        {benefitItems.length > 0 && (
          <div className="mt-4">
            <SectionCard
              iconBg="bg-[#EAF3DE]"
              iconContent={<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M8 3v10" stroke="#3B6D11" strokeWidth="1.5" strokeLinecap="round"/></svg>}
              title="What you receive"
            >
              <div className="flex flex-col gap-2">
                {benefitItems.map(b => <CheckItem key={b} text={b} />)}
              </div>
            </SectionCard>
          </div>
        )}

        {/* How to apply */}
        {scheme.howToApply && (
          <div className="mt-4">
            <SectionCard
              iconBg="bg-[#EEEDFE]"
              iconContent={<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 13V8l5-6 5 6v5H3Z" stroke="#534AB7" strokeWidth="1.4" strokeLinejoin="round"/><path d="M6 13V10h4v3" stroke="#534AB7" strokeWidth="1.3" strokeLinejoin="round"/></svg>}
              title="How to apply"
            >
              <div className="flex flex-col gap-0">
                <ApplyStep number={1} title="Self-referral or referral" desc="Walk in directly, call, or get referred by a social worker or court." />
                <ApplyStep number={2} title="Intake assessment" desc={scheme.howToApply} />
                <ApplyStep number={3} title="Begin your programme" desc="Sessions scheduled based on your needs and availability." />
              </div>
            </SectionCard>
          </div>
        )}

        {/* Contact */}
        {scheme.contact && scheme.contact.length > 0 && (
          <div className="mt-4">
            <SectionCard
              iconBg="bg-[#F1EFE8]"
              iconContent={<svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 4h10v8H3z" stroke="#5F5E5A" strokeWidth="1.3"/><path d="M3 4l5 5 5-5" stroke="#5F5E5A" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></svg>}
              title="Contact &amp; locations"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {scheme.contact.slice(0, 4).map((c, i) => (
                  <div key={i} className="bg-[#f7fafd] border border-[#e4edf7] rounded-lg px-3.5 py-3 text-sm flex flex-col gap-1.5">
                    {c.planningArea && <p className="text-[9px] font-bold uppercase tracking-wide text-[#B4B2A9]">{c.planningArea}</p>}
                    {c.address && <p className="text-[#5F5E5A] text-xs leading-snug">📍 {c.address}</p>}
                    {c.phones?.map(p => <a key={p} href={`tel:${p}`} className="text-[#185FA5] text-xs hover:underline">📞 {p}</a>)}
                    {c.emails?.map(e => <a key={e} href={`mailto:${e}`} className="text-[#185FA5] text-xs hover:underline break-all">✉️ {e}</a>)}
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        )}

        {/* Discovery CTA pair */}
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-[#042C53] to-[#185FA5] rounded-2xl px-5 py-5 flex flex-col">
            <div className="w-9 h-9 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center mb-3">
              <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M4 4h12v9H4z" stroke="rgba(255,255,255,0.9)" strokeWidth="1.4" rx="2"/><path d="M7 13l-3 3V13" stroke="rgba(255,255,255,0.9)" strokeWidth="1.4" strokeLinejoin="round"/></svg>
            </div>
            <p className="font-[var(--font-head)] text-[13.5px] font-bold text-white mb-1.5">Not sure this is right?</p>
            <p className="text-xs text-white/65 leading-relaxed mb-4 flex-1">Chat with our AI to find schemes matched to your specific situation.</p>
            <Link href="/" className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#EF9F27] text-white text-xs font-semibold hover:bg-[#BA7517] transition-colors">
              Chat with AI →
            </Link>
          </div>
          <div className="bg-white border-[1.5px] border-[#e4edf7] rounded-2xl px-5 py-5 flex flex-col shadow-[0_2px_8px_rgba(4,44,83,0.06)]">
            <div className="w-9 h-9 rounded-xl bg-[#E6F1FB] border border-[#B5D4F4] flex items-center justify-center mb-3">
              <svg width="16" height="16" viewBox="0 0 12 12" fill="none"><rect x="1" y="1" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2"/><rect x="7" y="1" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2"/><rect x="1" y="7" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2"/><rect x="7" y="7" width="4" height="4" rx="1" stroke="#185FA5" strokeWidth="1.2"/></svg>
            </div>
            <p className="font-[var(--font-head)] text-[13.5px] font-bold text-[#042C53] mb-1.5">Prefer to browse?</p>
            <p className="text-xs text-[#5F5E5A] leading-relaxed mb-4 flex-1">Explore 500+ schemes filtered by category, location, and age group.</p>
            <Link href="/explore" className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#185FA5] text-white text-xs font-semibold hover:bg-[#0C447C] transition-colors">
              Explore all schemes →
            </Link>
          </div>
        </div>

        {/* Footer note */}
        <div className="mt-6 text-center text-xs text-[#B4B2A9]">
          {scheme.lastUpdated && <>Last updated {scheme.lastUpdated} · </>}
          <Link href="/feedback" className="text-[#378ADD] hover:underline">Report incorrect information</Link>
        </div>
      </div>
    </div>
  );
}
