"use client"

import { motion } from "framer-motion"
import { useLanguage, type Locale } from "@/lib/landing-i18n"
import { cn } from "@/lib/utils"

const languages: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "zh", label: "中文" },
]

export function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale } = useLanguage()

  return (
    <div
      className={cn(
        "flex items-center rounded-full bg-[#E6F1FB] border border-[#B5D4F4] p-1",
        className
      )}
      role="radiogroup"
      aria-label="Select language"
    >
      {languages.map((lang) => (
        <button
          key={lang.code}
          role="radio"
          aria-checked={locale === lang.code}
          onClick={() => setLocale(lang.code)}
          className={cn(
            "relative px-3 py-1 text-sm font-medium rounded-full transition-colors duration-200 cursor-pointer",
            locale === lang.code ? "text-[#042C53]" : "text-[#B4B2A9] hover:text-[#185FA5]"
          )}
        >
          {locale === lang.code && (
            <motion.div
              layoutId="lang-toggle-active"
              className="absolute inset-0 rounded-full bg-white shadow-sm border border-[#B5D4F4]"
              transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
            />
          )}
          <span className="relative z-10">{lang.label}</span>
        </button>
      ))}
    </div>
  )
}
