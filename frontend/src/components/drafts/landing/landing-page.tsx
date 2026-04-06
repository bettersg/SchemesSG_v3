"use client";
import { useChat } from "@/providers";
import { getSchemes } from "@/lib/schemes";
import Image from "next/image";
import Link from "next/link";
import { useRef, useState } from "react";
import { Spinner } from "@heroui/react";
import SASW from "@/assets/sasw.png";
import CareCorner from "@/assets/carecorner.png";

const CATEGORY_CHIPS = [
  { label: "Financial Aid", emoji: "💰" },
  { label: "Healthcare", emoji: "🏥" },
  { label: "Mental Health", emoji: "🧠" },
  { label: "Family Support", emoji: "👨‍👩‍👧" },
  { label: "Housing", emoji: "🏠" },
  { label: "Employment", emoji: "💼" },
  { label: "Food Assistance", emoji: "🍚" },
  { label: "Education", emoji: "📚" },
];

const MARQUEE_AGENCIES = [
  "HDB", "Ministry of Health", "Ministry of Social & Family",
  "CPF Board", "Care Corner SG", "SG Enable",
  "Agency for Integrated Care", "SINDA", "CDAC", "AWWA",
];

const FEATURES = [
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M3 5h16M3 9h10M3 13h13M3 17h8" stroke="#185FA5" strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
    ),
    bg: "bg-[#E6F1FB]",
    title: "Describe your situation",
    desc: "Type naturally — no forms. Our AI understands context and finds what kind of support you need.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M11 3L13.5 8.5L19.5 9.5L15 14L16 20L11 17L6 20L7 14L2.5 9.5L8.5 8.5L11 3Z" stroke="#BA7517" strokeWidth="1.8" strokeLinejoin="round"/>
      </svg>
    ),
    bg: "bg-[#FAEEDA]",
    title: "Get matched schemes",
    desc: "A personalised list of schemes with eligibility, benefits, and how to apply — right in the chat.",
  },
  {
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M5 17L17 5M12 5h5v5" stroke="#534AB7" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    bg: "bg-[#EEEDFE]",
    title: "Take action directly",
    desc: "Contact agencies, get referral guidance, or share details with a social worker without leaving the page.",
  },
];

export default function LandingPage() {
  const { setMessages, setSchemes, setSessionId } = useChat();
  const [isLoading, setIsLoading] = useState(false);
const [userQuery, setUserQuery] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSearch = async (query?: string) => {
    const q = query ?? userQuery;
    if (!q.trim()) return;
    setIsLoading(true);
    const { reader } = await getSchemes(q);
	console.log(reader);
    setTotalCount(totalCount);
    setNextCursor(nextCursor);
    setUserQuery(q);
    if (sessionId) {
      setSessionId(sessionId);
      setMessages([{ type: "user", text: q }]);
    }
    if (schemesRes.length > 0) setSchemes(schemesRes);
    setIsLoading(false);
  };

  const handleChipClick = (label: string) => {
    const q = `I need ${label.toLowerCase()} support`;
    setUserQuery(q);
    handleSearch(q);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* ── HERO ── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#f0f6ff] via-[#e8f4fe] to-[#f5f0ff] pt-16 pb-14 px-4 sm:px-8 lg:px-16">
        {/* Background blobs */}
        <div className="pointer-events-none absolute top-[-80px] right-[-80px] w-[420px] h-[420px] rounded-full bg-[radial-gradient(circle,rgba(55,138,221,0.12)_0%,transparent_70%)]" />
        <div className="pointer-events-none absolute bottom-[-60px] left-[-40px] w-[280px] h-[280px] rounded-full bg-[radial-gradient(circle,rgba(127,119,221,0.08)_0%,transparent_70%)]" />

        <div className="relative max-w-[640px] mx-auto text-center">
          {/* Live badge */}
          <div className="inline-flex items-center gap-2 bg-[#E6F1FB] border border-[#B5D4F4] rounded-full px-3 py-1.5 text-xs font-semibold text-[#185FA5] mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1D9E75] animate-pulse" />
            500+ schemes · 200+ agencies · 100% anonymous
          </div>

          <h1 className="font-[var(--font-head)] font-extrabold text-[2.6rem] sm:text-[3.2rem] leading-[1.1] tracking-tight text-[#042C53] mb-4">
            Find the <span className="text-[#185FA5]">Right Schemes</span>,<br /> 
			All in One Place
          </h1>

          <p className="text-[#5F5E5A] text-base sm:text-lg mb-8 leading-relaxed">
            Singapore&apos;s AI-powered directory of social assistance schemes — for individuals, families, and the professionals who support them.
          </p>

          {/* Search bar */}
          <div className="bg-white border-2 border-[#d0e4f7] rounded-2xl flex items-start gap-3 p-2 pl-4 shadow-[0_4px_24px_rgba(24,95,165,0.10)] mb-5 text-left">
            <svg className="mt-2.5 shrink-0" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="7" cy="7" r="5.5" stroke="#B4B2A9" strokeWidth="1.5"/>
              <path d="M11 11L14.5 14.5" stroke="#B4B2A9" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <textarea
              ref={inputRef}
              value={userQuery}
              onChange={(e) => setUserQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSearch(); }
              }}
              placeholder="E.g. I am a cancer patient in need of financial assistance and food support."
              className="flex-1 resize-none bg-transparent outline-none text-sm text-[#444441] placeholder:text-[#B4B2A9] min-h-[48px] pt-1.5 leading-relaxed"
              rows={2}
            />
            <button
              onClick={() => handleSearch()}
              disabled={isLoading}
              className="shrink-0 px-5 py-2.5 rounded-xl bg-[#185FA5] text-white text-sm font-semibold hover:bg-[#0C447C] transition-colors flex items-center gap-2 mt-0.5 disabled:opacity-60"
            >
              {isLoading ? <Spinner size="sm" color="white" /> : (
                <>
                  Search
                  <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                    <path d="M14 7H0M8 1l6 6-6 6" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </>
              )}
            </button>
          </div>

          {/* Category chips */}
          <div className="flex flex-wrap gap-2 justify-center">
            {CATEGORY_CHIPS.map((c) => (
              <button
                key={c.label}
                onClick={() => handleChipClick(c.label)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-[#e0eaf5] rounded-full text-sm font-medium text-[#444441] hover:border-[#B5D4F4] hover:text-[#185FA5] hover:bg-[#E6F1FB] transition-all"
              >
                <span>{c.emoji}</span> {c.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ── AGENCY MARQUEE ── */}
      <div className="relative overflow-hidden border-y border-[#e8eef6] bg-white py-4 marquee-wrap">
        <div className="faded-element">
          <div className="marquee-track items-center">
            {[...MARQUEE_AGENCIES, ...MARQUEE_AGENCIES].map((name, i) => (
              <div key={i} className="flex items-center gap-2.5 px-4 text-xs font-semibold text-[#B4B2A9] whitespace-nowrap">
                <div className="w-7 h-7 rounded-md bg-[#F1EFE8] border border-[#D3D1C7] flex items-center justify-center text-[8px] font-extrabold text-[#5F5E5A]">
                  {name.slice(0, 3).toUpperCase()}
                </div>
                {name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── STATS ── */}
      <div className="bg-white border-b border-[#e8eef6]">
        <div className="max-w-[960px] mx-auto grid grid-cols-2 sm:grid-cols-4">
          {[
            { n: "500+", l: "Social schemes listed" },
            { n: "200+", l: "Partner agencies" },
            { n: "1,200+", l: "Monthly users" },
            { n: "100%", l: "Anonymous & private" },
          ].map((s) => (
            <div key={s.l} className="py-6 px-4 text-center border-r last:border-r-0 border-[#e8eef6] sm:py-8">
              <div className="font-[var(--font-head)] text-3xl font-extrabold text-[#185FA5]">{s.n}</div>
              <div className="text-xs text-[#B4B2A9] mt-1">{s.l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── HOW IT WORKS ── */}
      <section className="bg-[#f7f9fc] py-16 px-4 sm:px-8 lg:px-16">
        <div className="max-w-[960px] mx-auto">
          <p className="text-xs font-bold uppercase tracking-widest text-[#378ADD] mb-3">How it works</p>
          <h2 className="font-[var(--font-head)] text-3xl sm:text-4xl font-bold text-[#042C53] mb-3 leading-tight">
            One conversation.<br />The right schemes.
          </h2>
          <p className="text-[#5F5E5A] text-base mb-10 max-w-[500px] leading-relaxed">
            Tell our AI what you&apos;re going through. It finds the most relevant support and helps you understand how to access it.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-white border-2 border-[#eef2f7] rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#378ADD] to-[#7F77DD]" />
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${f.bg}`}>
                  {f.icon}
                </div>
                <h3 className="font-[var(--font-head)] text-[15px] font-semibold text-[#042C53] mb-2">{f.title}</h3>
                <p className="text-sm text-[#5F5E5A] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PARTNERS ── */}
      <section className="bg-[#f7f9fc] border-t border-[#e8eef6] py-12 px-4">
        <div className="max-w-[960px] mx-auto">
          <p className="text-xs font-bold uppercase tracking-widest text-[#B4B2A9] text-center mb-6">Our Partners</p>
          <div className="flex justify-center items-center gap-10 flex-wrap">
            <Link href="https://sasw.org.sg" target="_blank" rel="noopener noreferrer">
              <Image src={SASW} alt="SASW" height={60} unoptimized priority className="opacity-70 hover:opacity-100 transition-opacity" />
            </Link>
            <Link href="https://www.carecorner.org.sg/" target="_blank" rel="noopener noreferrer">
              <Image src={CareCorner} alt="Care Corner" height={60} unoptimized priority className="opacity-70 hover:opacity-100 transition-opacity" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── CTA FOOTER ── */}
      <section className="bg-gradient-to-br from-[#042C53] to-[#185FA5] py-16 px-4 text-center">
        <h2 className="font-[var(--font-head)] text-3xl sm:text-4xl font-bold text-white mb-3 leading-tight">
          Find the right support today.
        </h2>
        <p className="text-white/70 text-base mb-8">Anonymous and free. No sign-up required.</p>
        <div className="flex flex-wrap gap-3 justify-center">
          <button
            onClick={() => inputRef.current?.focus()}
            className="px-7 py-3 rounded-xl bg-[#EF9F27] text-white text-[15px] font-bold hover:bg-[#BA7517] transition-colors"
          >
            Chat with AI →
          </button>
          <Link
            href="/explore"
            className="px-7 py-3 rounded-xl bg-white/12 text-white text-[15px] font-semibold border border-white/20 hover:bg-white/20 transition-colors"
          >
            Browse all schemes
          </Link>
        </div>
      </section>

      {/* ── MINIMAL FOOTER ── */}
      <footer className="bg-[#042C53] border-t border-white/10 py-6 px-4 text-center">
        <div className="font-[var(--font-head)] font-bold text-sm text-white mb-1">SchemesSG</div>
        <div className="text-xs text-white/35">Built by the community, for the community · Supported by Better.sg</div>
      </footer>
    </div>
  );
}
