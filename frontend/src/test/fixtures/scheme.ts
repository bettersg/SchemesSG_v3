import type { Scheme } from "@/types/types";

export function makeScheme(overrides: Partial<Scheme> = {}): Scheme {
  return {
    schemeId: "scheme-1",
    schemeType: [],
    schemeName: "Support Scheme",
    agency: "Support Agency",
    description: "",
    targetAudience: [],
    scrapedText: "",
    benefits: [],
    link: "",
    image: "",
    searchBooster: "",
    query: "",
    planningArea: "",
    summary: "",
    contact: [],
    howToApply: "",
    eligibilityText: "",
    lastUpdated: "",
    serviceArea: "",
    ...overrides,
  };
}
