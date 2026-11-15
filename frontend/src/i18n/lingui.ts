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

export async function activateLocale(locale: Locale) {
  if (locale !== "en" && !(locale in i18n.messages)) {
    const { messages } = await loaders[locale]();
    i18n.load(locale, messages);
  }
  i18n.activate(locale);
}

export { i18n };
