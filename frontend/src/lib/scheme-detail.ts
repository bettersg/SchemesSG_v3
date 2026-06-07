import { cache } from "react";
import { BranchContact, RawScheme, Scheme, SearchResponse } from "@/types/types";

type AnonymousTokenResponse = {
  idToken?: string;
  expiresIn?: string;
};

let cachedAnonymousToken: { token: string; expiresAt: number } | null = null;

const splitCsv = (v?: string | null): string[] | undefined => {
  if (!v) return undefined;
  const parts = v
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return parts.length ? parts : undefined;
};

const buildContacts = (raw: RawScheme): BranchContact[] => {
  const planningAreas = Array.isArray(raw.planning_area)
    ? raw.planning_area
    : raw.planning_area && raw.planning_area !== "No Location"
      ? [raw.planning_area]
      : undefined;

  if (planningAreas) {
    const maxContacts = Math.max(
      Array.isArray(raw.phone) ? raw.phone.length : 0,
      Array.isArray(raw.email) ? raw.email.length : 0,
      Array.isArray(raw.address) ? raw.address.length : 0,
    );

    if (maxContacts == 0) {
      return Array.from(new Set(planningAreas)).map((planningArea) => ({
        planningArea,
        phones: undefined,
        emails: undefined,
        address: undefined,
      }));
    }

    if (planningAreas.length == 1) {
      return [
        {
          planningArea: planningAreas[0],
          phones: Array.isArray(raw.phone) ? raw.phone : splitCsv(raw.phone),
          emails: Array.isArray(raw.email) ? raw.email : splitCsv(raw.email),
          address: Array.isArray(raw.address)
            ? raw.address[0]
            : (raw.address ?? undefined),
        },
      ];
    }

    return planningAreas.map((area, i) => {
      const phoneAt = Array.isArray(raw.phone) ? raw.phone[i] : raw.phone;
      const emailAt = Array.isArray(raw.email) ? raw.email[i] : raw.email;
      const addressAt = Array.isArray(raw.address)
        ? raw.address[i]
        : raw.address;
      return {
        planningArea: area,
        phones: splitCsv(phoneAt),
        emails: splitCsv(emailAt),
        address: addressAt || undefined,
      };
    });
  }

  const phones = splitCsv(
    Array.isArray(raw.phone) ? raw.phone.join(",") : raw.phone,
  );
  const emails = splitCsv(
    Array.isArray(raw.email) ? raw.email.join(",") : raw.email,
  );
  const address = Array.isArray(raw.address) ? raw.address[0] : raw.address;
  if (phones || emails || address) {
    return [{ phones, emails, address: address || undefined }];
  }
  return [];
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
  lastUpdated: raw.last_scraped_update
    ? new Date(raw.last_scraped_update._seconds * 1000).toLocaleString()
    : "",
});

async function getServerAnonymousToken(): Promise<string> {
  if (
    cachedAnonymousToken &&
    cachedAnonymousToken.expiresAt > Date.now() + 60_000
  ) {
    return cachedAnonymousToken.token;
  }

  const apiKey = process.env.NEXT_PUBLIC_FB_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NEXT_PUBLIC_FB_API_KEY");
  }

  const response = await fetch(
    `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ returnSecureToken: true }),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error("Unable to create anonymous Firebase session");
  }

  const data = (await response.json()) as AnonymousTokenResponse;
  if (!data.idToken) {
    throw new Error("Anonymous Firebase session did not return an ID token");
  }

  const expiresInMs = Number(data.expiresIn ?? 3600) * 1000;
  cachedAnonymousToken = {
    token: data.idToken,
    expiresAt: Date.now() + expiresInMs,
  };

  return data.idToken;
}

export const getSchemeById = cache(
  async (schemeId: string): Promise<Scheme | null> => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) {
      throw new Error("Missing NEXT_PUBLIC_API_BASE_URL");
    }

    const token = await getServerAnonymousToken();
    const response = await fetch(`${baseUrl}/schemes/${schemeId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      next: { revalidate: 86_400 },
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error(`Unable to fetch scheme ${schemeId}`);
    }

    const payload = (await response.json()) as { data?: RawScheme };
    if (!payload.data) {
      return null;
    }

    return {
      ...mapToFullScheme(payload.data),
      schemeId: payload.data.scheme_id || schemeId,
    };
  },
);

export const getSchemesForSitemap = cache(async (): Promise<Scheme[]> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    throw new Error("Missing NEXT_PUBLIC_API_BASE_URL");
  }

  const token = await getServerAnonymousToken();
  const response = await fetch(`${baseUrl}/schemes_search`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query:
        "financial assistance healthcare housing employment education family eldercare disability mental health food support social assistance",
      limit: 1000,
      top_k: 1000,
      similarity_threshold: 0,
      cursor: null,
    }),
    next: { revalidate: 86_400 },
  });

  if (!response.ok) {
    return [];
  }

  const payload = (await response.json()) as SearchResponse;
  const rawSchemes = payload.data
    ? Array.isArray(payload.data)
      ? payload.data
      : [payload.data]
    : [];

  const seen = new Set<string>();
  return rawSchemes
    .map((raw) => mapToFullScheme(raw as RawScheme))
    .filter((scheme) => {
      if (!scheme.schemeId || seen.has(scheme.schemeId)) {
        return false;
      }
      seen.add(scheme.schemeId);
      return true;
    });
});
