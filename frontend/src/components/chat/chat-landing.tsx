	"use client";
import { useChat } from "@/providers";
import { useRef, useState } from "react";
import { Spinner } from "@heroui/react";

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

export default function ChatLanding() {
	const { setMessages } = useChat();
	const [userQuery, setUserQuery] = useState('')
	const [isLoading, setIsLoading] = useState(false);
	const inputRef = useRef<HTMLTextAreaElement>(null);

	const handleSearch = async (query?: string) => {
		const q = query ?? userQuery;
		if (!q.trim()) return;
		setIsLoading(true);
		setMessages([{type: 'user', text: q}])
		setIsLoading(false);
	};

	const handleChipClick = (label: string) => {
		const q = `I need ${label.toLowerCase()} support`;
		setUserQuery(q);
		handleSearch(q);
	};
	return (
			<div className="w-full min-h-[calc(100vh-60px)] bg-white flex ">
			  {/* ── HERO ── */}
			  <section className="w-full relative overflow-hidden bg-gradient-to-br from-[#f0f6ff] via-[#e8f4fe] to-[#f5f0ff] pt-16 pb-14 px-4 sm:px-8 lg:px-16">
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
					Singapore&apos;s AI-powered directory of social assistance schemes
				  </p>
		
				  {/* Search bar */}
				  <div className="bg-white border-2 border-[#d0e4f7] rounded-2xl flex items-start gap-3 p-2 pl-4 shadow-[0_4px_24px_rgba(24,95,165,0.10)] mb-5 text-left">
					<svg className="mt-2.5 shrink-0" width="16" height="16" viewBox="0 0 16 16" fill="none">
					  {/* <circle cx="7" cy="7" r="5.5" stroke="#B4B2A9" strokeWidth="1.5"/> */}
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
					  {isLoading ? <Spinner size="sm"/> : (
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
		</div>
	);
}
