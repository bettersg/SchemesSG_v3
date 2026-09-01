import type {
  BranchContact,
  RawScheme,
  RawSchemeData,
  Scheme,
} from "@/types/types";

export const mapToScheme = (rawData: RawSchemeData): Scheme => ({
  schemeType: rawData["scheme_type"] || rawData["Scheme Type"] || [],
  schemeName: rawData["scheme"] || rawData["Scheme"] || "",
  targetAudience: rawData["who_is_it_for"] || rawData["Who's it for"] || [],
  agency: rawData["agency"] || rawData["Agency"] || "",
  description: rawData["description"] || rawData["Description"] || "",
  scrapedText: rawData["scraped_text"] || "",
  benefits: rawData["what_it_gives"] || rawData["What it gives"] || [],
  link: rawData["link"] || rawData["Link"] || "",
  image: rawData["image"] || rawData["Image"] || "",
  searchBooster:
    rawData["search_booster"] || rawData["search_booster(WL)"] || "",
  schemeId: rawData["scheme_id"] || "",
  query: rawData["query"] || "",
  planningArea: rawData["planning_area"] || "",
  summary: rawData["summary"] || "",
  contact: [],
  howToApply:
    (rawData as Record<string, string | undefined>)["how_to_apply"] ||
    (rawData as Record<string, string | undefined>)["How to apply"] ||
    "",
  eligibilityText:
    (rawData as Record<string, string | undefined>)["eligibility_text"] ||
    (rawData as Record<string, string | undefined>)["Eligibility"] ||
    "",
  lastUpdated:
    (rawData as Record<string, string | undefined>)["last_updated"] ||
    (rawData as Record<string, string | undefined>)["Last updated"] ||
    "",
  serviceArea:
    (rawData as Record<string, string | undefined>)["service_area"] ||
    (rawData as Record<string, string | undefined>)["Service area"] ||
    "",
});

const splitCsv = (value?: string | null): string[] | undefined => {
  if (!value) return undefined;
  const parts = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return parts.length ? parts : undefined;
};

// "No Location" is a dataset placeholder, not a planning-area label.
const cleanPlanningArea = (value?: string): string | undefined =>
  value && value !== "No Location" ? value : undefined;

// Scraped sources sometimes return obfuscation text instead of an email address.
const isRealEmail = (value: string): boolean =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

const cleanEmails = (emails?: string[]): string[] | undefined => {
  const valid = emails?.filter(isRealEmail);
  return valid && valid.length ? valid : undefined;
};

const buildContacts = (raw: RawScheme): BranchContact[] => {
  const planningAreas = Array.isArray(raw.planning_area)
    ? raw.planning_area
    : raw.planning_area
      ? [raw.planning_area]
      : undefined;

  if (planningAreas) {
    const fieldCount = (value?: string | string[] | null) =>
      Array.isArray(value) ? value.length : value ? 1 : 0;
    const maxContacts = Math.max(
      fieldCount(raw.phone),
      fieldCount(raw.email),
      fieldCount(raw.address),
    );

    if (maxContacts === 0) {
      // Keep real area labels, but do not render empty placeholder cards.
      return Array.from(new Set(planningAreas))
        .map(cleanPlanningArea)
        .filter((planningArea): planningArea is string => Boolean(planningArea))
        .map((planningArea) => ({
          planningArea,
          phones: undefined,
          emails: undefined,
          address: undefined,
        }));
    }

    if (planningAreas.length === 1) {
      return [
        {
          planningArea: cleanPlanningArea(planningAreas[0]),
          phones: Array.isArray(raw.phone) ? raw.phone : splitCsv(raw.phone),
          emails: cleanEmails(
            Array.isArray(raw.email) ? raw.email : splitCsv(raw.email),
          ),
          address: Array.isArray(raw.address)
            ? raw.address[0]
            : (raw.address ?? undefined),
        },
      ];
    }

    return planningAreas.map((planningArea, index) => {
      const phone = Array.isArray(raw.phone) ? raw.phone[index] : raw.phone;
      const email = Array.isArray(raw.email) ? raw.email[index] : raw.email;
      const address = Array.isArray(raw.address)
        ? raw.address[index]
        : raw.address;

      return {
        planningArea: cleanPlanningArea(planningArea),
        phones: splitCsv(phone),
        emails: cleanEmails(splitCsv(email)),
        address: address || undefined,
      };
    });
  }

  const phones = splitCsv(
    Array.isArray(raw.phone) ? raw.phone.join(",") : raw.phone,
  );
  const emails = cleanEmails(
    splitCsv(Array.isArray(raw.email) ? raw.email.join(",") : raw.email),
  );
  const address = Array.isArray(raw.address) ? raw.address[0] : raw.address;

  return phones || emails || address
    ? [{ phones, emails, address: address || undefined }]
    : [];
};

export const mapToFullScheme = (raw: RawScheme): Scheme => ({
  schemeId: raw.scheme_id || "",
  schemeName: raw.scheme || "",
  schemeType: raw.scheme_type || [],
  targetAudience: raw.who_is_it_for || [],
  agency: raw.agency || "",
  description: raw.llm_description || raw.description || "",
  scrapedText: raw.scraped_text || "",
  benefits: raw.what_it_gives || [],
  link: raw.link || "",
  image: raw.image || "",
  searchBooster: raw.search_booster || "",
  query: "",
  planningArea: raw.planning_area || "",
  summary: raw.summary || "",
  contact: buildContacts(raw),
  howToApply: raw.how_to_apply || "",
  eligibilityText: raw.eligibility || "",
  serviceArea:
    (raw.service_area !== "No Service Boundaries" && raw.service_area) || "",
  status: raw.status,
  mergedInto: raw.merged_into,
  lastUpdated: raw.last_scraped_update
    ? new Date(raw.last_scraped_update._seconds * 1000).toLocaleString()
    : "",
});
