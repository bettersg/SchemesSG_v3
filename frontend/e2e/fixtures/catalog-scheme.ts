import { expect, type BrowserContext, type Page } from "@playwright/test";
import type { RawScheme, RawSchemeData } from "../../src/types/types";
import {
  E2E_API_ORIGIN,
  interceptLandingResultsJourney,
} from "./landing-results";

export const SCHEME_DETAIL_ID = "bright-start-support";
export const EXTERNAL_SCHEME_URL = "https://support.example.test/bright-start";

export const SCHEME_DETAIL: RawScheme = {
  scheme_id: SCHEME_DETAIL_ID,
  scheme: "Bright Start Support",
  agency: "Family Services Singapore",
  scheme_type: ["Financial Assistance", "Family"],
  summary: "Help with essential costs while families regain stability.",
  llm_description:
    "Bright Start Support provides temporary help with essential household costs while families work towards stability.",
  who_is_it_for: ["Families with children", "Households facing income loss"],
  what_it_gives: ["Monthly essentials grant", "Support planning session"],
  eligibility:
    "Applicants must live in Singapore and complete a household needs assessment.",
  how_to_apply:
    "Apply online with identification and recent household income documents.",
  link: EXTERNAL_SCHEME_URL,
  planning_area: ["Central"],
  service_area: "Islandwide",
  phone: "+65 6123 4567",
  email: "help@brightstart.example.test",
  address: "10 Community Way, Singapore 123456",
  status: "active",
};

export const CATALOG_SCHEMES: RawSchemeData[] = [
  {
    scheme_id: SCHEME_DETAIL_ID,
    scheme: "Bright Start Support",
    agency: "Family Services Singapore",
    scheme_type: ["Financial Assistance", "Family"],
    summary: "Help with essential costs while families regain stability.",
    link: EXTERNAL_SCHEME_URL,
  },
  {
    scheme_id: "daily-needs-grant",
    scheme: "Daily Needs Grant",
    agency: "Community Assistance Network",
    scheme_type: ["Financial Assistance"],
    summary: "Short-term support for groceries and household essentials.",
    link: "https://support.example.test/daily-needs",
  },
  {
    scheme_id: "family-care-fund",
    scheme: "Family Care Fund",
    agency: "Care Partnership Office",
    scheme_type: ["Financial Assistance", "Family & Children"],
    summary: "Practical support for households with ongoing care needs.",
    link: "https://support.example.test/family-care",
  },
];

export type PublicFixtureRequest = {
  resource: "catalog" | "scheme";
  method: string;
  authorization: string | null;
  /** Whether the page or the server made the read. */
  initiator: "browser" | "server";
  category?: string | null;
  cursor?: string | null;
  limit?: string | null;
  schemeId?: string;
};

/**
 * Read the requests the public build fixture server has served so far.
 *
 * Catalog and scheme reads now happen inside Server Components, so a
 * browser-side interceptor never sees them. The fixture server records them
 * instead, which is also what lets a spec assert that the public API is called
 * without an Authorization header.
 */
export async function readPublicFixtureRequests(): Promise<
  PublicFixtureRequest[]
> {
  const response = await fetch(`${E2E_API_ORIGIN}/__fixture/requests`);
  expect(response.ok).toBe(true);
  const payload = (await response.json()) as {
    requests: PublicFixtureRequest[];
  };
  return payload.requests;
}

async function resetPublicFixtureRequests(): Promise<void> {
  const response = await fetch(`${E2E_API_ORIGIN}/__fixture/requests`, {
    method: "DELETE",
  });
  expect(response.ok).toBe(true);
}

/**
 * Fail loudly if the TypeScript expectations above drift from the schemes the
 * fixture server actually serves, instead of leaving a spec to fail later with
 * an unhelpful "link not visible".
 */
async function assertFixtureSchemesMatch(): Promise<void> {
  const response = await fetch(`${E2E_API_ORIGIN}/catalog?limit=20`);
  expect(response.ok).toBe(true);
  const payload = (await response.json()) as { data: RawSchemeData[] };
  for (const expected of CATALOG_SCHEMES) {
    const served = payload.data.find(
      (item) => item.scheme_id === expected.scheme_id,
    );
    expect(
      served,
      `public-build-fixture.mjs is missing scheme ${expected.scheme_id}`,
    ).toBeDefined();
    expect(served?.scheme).toBe(expected.scheme);
    expect(served?.agency).toBe(expected.agency);
    expect(served?.link).toBe(expected.link);
  }
}

export async function interceptCatalogSchemeJourney(page: Page) {
  const landingNetwork = await interceptLandingResultsJourney(page);
  await assertFixtureSchemesMatch();
  await resetPublicFixtureRequests();

  return { ...landingNetwork, readPublicFixtureRequests };
}

export async function interceptSchemeDetailJourney(context: BrowserContext) {
  await context.route(EXTERNAL_SCHEME_URL, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: '<!doctype html><html lang="en"><title>Bright Start application</title><body><main><h1>Bright Start application</h1></main></body></html>',
    });
  });
}
