import { createContext, useContext, useState, useCallback, useMemo } from "react"
import type { Locale, Translations } from "./types"
import { en } from "./translations/en"
import { zh } from "./translations/zh"

const translationMap: Record<Locale, Translations> = { en, zh }

interface LanguageContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: Translations
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    try {
      const saved = localStorage.getItem("schemes-lang") as Locale | null
      if (saved && saved in translationMap) return saved
    } catch {
      // localStorage unavailable (SSR, private browsing, etc.)
    }
    return "en"
  })

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale)
    try {
      localStorage.setItem("schemes-lang", newLocale)
    } catch {
      // ignore
    }
    document.documentElement.lang = newLocale === "zh" ? "zh-Hans" : newLocale
  }, [])

  const value = useMemo(
    () => ({ locale, setLocale, t: translationMap[locale] }),
    [locale, setLocale]
  )

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider")
  return ctx
}
