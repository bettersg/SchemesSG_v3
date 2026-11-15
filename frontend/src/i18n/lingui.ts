import { i18n } from "@lingui/core";
import { messages as enMessages } from "@/locales/en/messages";
import type { Locale } from "@/lib/landing-i18n";

// English is bundled and active from the first render, so prerendered HTML is
// English (the server cannot know a visitor's saved language). Other locales
// load on demand when the visitor switches.
i18n.load("en", enMessages);
i18n.activate("en");

const loaders: Record<
  Exclude<Locale, "en">,
  () => Promise<{ messages: typeof enMessages }>
> = {
  zh: () => import("@/locales/zh/messages"),
  ta: () => import("@/locales/ta/messages"),
  ms: () => import("@/locales/ms/messages"),
};

// Lingui 6's `i18n.messages` holds only the active catalog, so loaded locales
// are tracked here.
const loaded = new Set<Locale>(["en"]);
let requested: Locale = "en";

/**
 * Loads a locale's catalog once and activates it, unless a newer switch was
 * requested while it loaded. Rejects if the catalog fails to load, leaving the
 * active locale unchanged.
 */
export async function activateLocale(locale: Locale) {
  requested = locale;
  if (locale !== "en" && !loaded.has(locale)) {
    const { messages } = await loaders[locale]();
    i18n.load(locale, messages);
    loaded.add(locale);
  }
  if (requested === locale) i18n.activate(locale);
}

export { i18n };
