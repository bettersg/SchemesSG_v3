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

// The saved locale is an external store rather than component state, so that
// the server snapshot and the client snapshot can legitimately differ.
//
// These pages are prerendered, so the server has no way to know a visitor's
// language and always emits English. Reading localStorage in a useState
// initialiser therefore made every translated string a hydration mismatch for a
// returning Chinese visitor. useSyncExternalStore is built for this: React uses
// `getServerSnapshot` while hydrating, then re-reads the store and re-renders,
// which is a deliberate update rather than a mismatch. The cost is a brief
// flash of English, which is the trade a statically rendered site has to make.
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

  // Mirrors the locale onto <html lang>, which the CSS minimum font size for
  // Chinese selects on. Setting it only inside setLocale missed the case that
  // matters most: a restored preference renders Chinese while the document
  // still claims English, so the floor never applied and assistive tech read
  // the wrong language.
  useEffect(() => {
    const langMap: Record<Locale, string> = {
      en: "en",
      zh: "zh-Hans",
      ta: "ta",
      ms: "ms",
    }
    document.documentElement.lang = langMap[locale]
    void activateLocale(locale)
  }, [locale])

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
