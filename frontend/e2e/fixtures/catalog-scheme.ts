import type { BrowserContext, Page } from "@playwright/test";
import type { NextFixture } from "next/experimental/testmode/playwright";
import type { RawScheme, RawSchemeData } from "../../src/types/types";
import {
  E2E_API_ORIGIN,
  E2E_AUTH_TOKEN,
  E2E_FIREBASE_CONFIG,
  interceptLandingResultsJourney,
} from "./landing-results";

export const SCHEME_DETAIL_ID = "bright-start-support";
export const EXTERNAL_SCHEME_URL =
  "https://support.example.test/bright-start";

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

export async function interceptCatalogSchemeJourney(
  page: Page,
  { holdInitialCatalog = false }: { holdInitialCatalog?: boolean } = {},
) {
  const landingNetwork = await interceptLandingResultsJourney(page);
  let releaseInitialCatalog = () => {};
  const initialCatalogGate = holdInitialCatalog
    ? new Promise<void>((resolve) => {
        releaseInitialCatalog = resolve;
      })
    : Promise.resolve();
  const catalogRequests: Array<{
    authorization: string | undefined;
    category: string | null;
    limit: string | null;
    method: string;
  }> = [];

  await page.route(
    (url) => url.origin === E2E_API_ORIGIN && url.pathname === "/catalog",
    async (route) => {
      const request = route.request();
      const requestedHeaders =
        request.headers()["access-control-request-headers"] ??
        "authorization, content-type";
      const corsHeaders = {
        "access-control-allow-headers": requestedHeaders,
        "access-control-allow-methods": "GET, OPTIONS",
        "access-control-allow-origin": "*",
      };

      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers: corsHeaders });
        return;
      }

      const url = new URL(request.url());
      const category = url.searchParams.get("category");
      catalogRequests.push({
        authorization: request.headers().authorization,
        category,
        limit: url.searchParams.get("limit"),
        method: request.method(),
      });
      const schemes = category === "education" ? [] : CATALOG_SCHEMES;
      if (category === "financial assistance") {
        await initialCatalogGate;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: corsHeaders,
        body: JSON.stringify({
          data: schemes,
          has_more: false,
          total_count: schemes.length,
        }),
      });
    },
  );

  return { ...landingNetwork, catalogRequests, releaseInitialCatalog };
}

function authResponse(operation: "lookup" | "signUp") {
  const corsHeaders = {
    "access-control-allow-headers": "authorization, content-type",
    "access-control-allow-methods": "POST, OPTIONS",
    "access-control-allow-origin": "*",
    "content-type": "application/json",
  };

  return new Response(
    JSON.stringify(
      operation === "signUp"
        ? {
            expiresIn: "3600",
            idToken: E2E_AUTH_TOKEN,
            kind: "identitytoolkit#SignupNewUserResponse",
            localId: "e2e-anonymous-user",
            refreshToken: "e2e-refresh-token",
          }
        : {
            kind: "identitytoolkit#GetAccountInfoResponse",
            users: [
              {
                createdAt: "1893456000000",
                lastLoginAt: "1893456000000",
                localId: "e2e-anonymous-user",
                providerUserInfo: [],
              },
            ],
          },
    ),
    { status: 200, headers: corsHeaders },
  );
}

export async function interceptSchemeDetailJourney(
  next: NextFixture,
  context: BrowserContext,
) {
  const schemeRequests: Array<{
    authorization: string | null;
    method: string;
    schemeId: string;
  }> = [];

  next.onFetch(async (request) => {
    const url = new URL(request.url);
    if (
      url.hostname === "identitytoolkit.googleapis.com" &&
      ["/v1/accounts:lookup", "/v1/accounts:signUp"].includes(url.pathname)
    ) {
      return authResponse(
        url.pathname.endsWith(":lookup") ? "lookup" : "signUp",
      );
    }

    if (url.origin === E2E_API_ORIGIN && url.pathname.startsWith("/schemes/")) {
      const schemeId = url.pathname.slice("/schemes/".length);
      schemeRequests.push({
        authorization: request.headers.get("authorization"),
        method: request.method,
        schemeId,
      });
      return new Response(
        JSON.stringify({
          data: schemeId === SCHEME_DETAIL_ID ? SCHEME_DETAIL : undefined,
        }),
        {
          status: schemeId === SCHEME_DETAIL_ID ? 200 : 404,
          headers: { "content-type": "application/json" },
        },
      );
    }

    return undefined;
  });

  await context.route(EXTERNAL_SCHEME_URL, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<!doctype html><html lang=\"en\"><title>Bright Start application</title><body><main><h1>Bright Start application</h1></main></body></html>",
    });
  });

  return {
    firebaseProjectId: E2E_FIREBASE_CONFIG.projectId,
    schemeRequests,
  };
}
