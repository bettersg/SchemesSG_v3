import { motion } from "motion/react"
import { useLanguage, type Locale } from "@/i18n"
import { cn } from "@/lib/utils"

const languages: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "zh", label: "\u4E2D\u6587" },
  // Future: { code: "ms", label: "BM" },
  // Future: { code: "ta", label: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD" },
]

export function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale } = useLanguage()

  return (
    <div
      className={cn(
        "flex items-center rounded-full bg-neutral-100 border border-neutral-200/60 p-1",
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
            locale === lang.code
              ? "text-neutral-900"
              : "text-neutral-400 hover:text-neutral-600"
          )}
        >
          {locale === lang.code && (
            <motion.div
              layoutId="lang-toggle-active"
              className="absolute inset-0 rounded-full bg-white shadow-sm border border-neutral-200/60"
              transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
            />
          )}
          <span className="relative z-10">{lang.label}</span>
        </button>
      ))}
    </div>
  )
}
