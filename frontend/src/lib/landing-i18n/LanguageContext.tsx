"use client"

import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react"
import { I18nProvider } from "@lingui/react"
import { activateLocale, i18n } from "@/i18n/lingui"
import type { Locale } from "./types"

const LOCALES: readonly Locale[] = ["en", "zh", "ta", "ms"]

interface LanguageContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

const STORAGE_KEY = "schemes-lang"

// The saved locale is an external store, not component state, because pages are
// prerendered in English: the server can't know a visitor's language. React
// hydrates with `getServerSnapshot`, then re-renders in the saved language, so
// a returning visitor sees a brief flash of English but no hydration mismatch.
let cached: Locale | null = null
const listeners = new Set<() => void>()

function getSnapshot(): Locale {
  if (cached) return cached
  try {
    const saved = localStorage.getItem(STORAGE_KEY) as Locale | null
    if (saved && LOCALES.includes(saved)) cached = saved
  } catch {
    // localStorage unavailable (private browsing, etc.)
  }
  return (cached ??= "en")
}

function getServerSnapshot(): Locale {
  return "en"
}

// A change in another tab arrives as a `storage` event (the tab that made it
// gets none), so every open tab switches together. A null key means storage
// was cleared.
function subscribe(onChange: () => void) {
  listeners.add(onChange)
  const onStorage = (event: StorageEvent) => {
    if (event.key !== null && event.key !== STORAGE_KEY) return
    cached = null
    onChange()
  }
  window.addEventListener("storage", onStorage)
  return () => {
    listeners.delete(onChange)
    window.removeEventListener("storage", onStorage)
  }
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  const setLocale = useCallback((newLocale: Locale) => {
    cached = newLocale
    try {
      localStorage.setItem(STORAGE_KEY, newLocale)
    } catch {
      // ignore
    }
    listeners.forEach((notify) => notify())
  }, [])

  // Mirrors the locale onto <html lang> on every change, including a preference
  // restored on load: the Chinese and Tamil size floors and screen readers use
  // it.
  useEffect(() => {
    const langMap: Record<Locale, string> = {
      en: "en",
      zh: "zh-Hans",
      ta: "ta",
      ms: "ms",
    }
    document.documentElement.lang = langMap[locale]
    activateLocale(locale).catch((error: unknown) => {
      console.error(`Could not load the ${locale} translations`, error)
      // Fall back to the language still on screen, unless a newer choice
      // has replaced this one.
      if (getSnapshot() === locale) setLocale(i18n.locale as Locale)
    })
  }, [locale, setLocale])

  const value = useMemo(
    () => ({ locale, setLocale }),
    [locale, setLocale]
  )

  return (
    <LanguageContext.Provider value={value}>
      <I18nProvider i18n={i18n}>{children}</I18nProvider>
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error("useLanguage must be used within LanguageProvider")
  return ctx
}
