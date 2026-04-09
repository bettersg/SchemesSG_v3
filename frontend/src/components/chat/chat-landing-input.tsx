import { useLanguage } from '@/lib/landing-i18n';
import { motion } from 'framer-motion'
import { ArrowRight, Search } from 'lucide-react';
import { SubmitEventHandler, useRef } from 'react';

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

interface ChatLandingInputProps {
  query: string;
  setQuery: (q: string) => void;
  handleSubmit: (e: SubmitEvent) => void;
}

function ChatLandingInput({query, setQuery, handleSubmit}: ChatLandingInputProps) {
	const { t } = useLanguage()
  const btnRef = useRef<HTMLButtonElement>(null)
  const handleChipClick = (label: string) => {
		const q = `I need ${label.toLowerCase()} support`;
		setQuery(q);
		btnRef?.current?.click();
	};

	return (
		<div className="flex flex-col items-center justify-center text-center">
          {/* Headline */}
          <motion.h1
            className="font-serif text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl lg:text-[4.5rem] xl:text-[5rem]"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
          >
            {t.hero.headline.split("\n").map((line, i, arr) => (
              <span key={i}>
                {line}
                {i < arr.length - 1 && <br />}
              </span>
            ))}
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            className="mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-neutral-500"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {t.hero.subtitle}
          </motion.p>

          {/* Search bar */}
          <motion.form
            onSubmit={handleSubmit}
            className="mt-8 w-full max-w-lg flex flex-col gap-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
          >
            <div className="relative flex items-center rounded-full bg-white border border-neutral-300 shadow-[0_4px_24px_rgba(0,0,0,0.08)] hover:shadow-[0_6px_32px_rgba(0,0,0,0.12)] transition-shadow duration-300 focus-within:ring-2 focus-within:ring-amber-400/50 focus-within:border-amber-400">
              <Search className="absolute left-5 h-5 w-5 text-neutral-500 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent py-4 pl-14 pr-14 text-[15px] text-neutral-800 placeholder:text-neutral-500 focus:outline-none rounded-full"
              />
              <button
                type="submit"
                className="absolute right-2 flex h-10 w-10 items-center justify-center rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 transition-colors duration-200 cursor-pointer shadow-sm"
                aria-label={t.a11y.search}
              >
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
            {/* <p className="mt-3 text-xs text-neutral-400">
              {t.hero.searchHint}
            </p> */}
            {/* Category chips */}
				  <div className="flex flex-wrap gap-2 justify-center">
					{CATEGORY_CHIPS.map((c) => (
					  <button
						key={c.label}
						onClick={() => handleChipClick(c.label)}
            ref={btnRef}
						className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border-2 border-[#e0eaf5] rounded-full text-sm font-medium text-[#444441] hover:border-[#B5D4F4] hover:text-[#185FA5] hover:bg-[#E6F1FB] transition-all"
					  >
						<span>{c.emoji}</span> {c.label}
					  </button>
					))}
				  </div>
          </motion.form>
        </div>
	);
}

export default ChatLandingInput;