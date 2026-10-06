"use client"

import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react"
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
    if (saved && saved in translationMap) cached = saved
  } catch {
    // localStorage unavailable (private browsing, etc.)
  }
  return (cached ??= "en")
}

function getServerSnapshot(): Locale {
  return "en"
}

function subscribe(onChange: () => void) {
  listeners.add(onChange)
  return () => {
    listeners.delete(onChange)
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
    document.documentElement.lang = locale === "zh" ? "zh-Hans" : locale
  }, [locale])

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
