import type { Page, Request } from "@playwright/test";
import type { RawSchemeData } from "../../src/types/types";

export const E2E_API_ORIGIN = "https://api.e2e.test";
export const E2E_FIREBASE_CONFIG = {
  apiKey: "e2e-api-key",
  appId: "1:123456789012:web:e2e000000000000000000",
  measurementId: "G-E2E000000",
  projectId: "schemessg-e2e",
} as const;

export const LANDING_QUERY = "I need help with household expenses";
export const LANDING_ANSWER =
  "I found two Singapore support schemes that may help with essential household costs.";
export const FOLLOW_UP = {
  label: "Compare eligibility",
  value: "Compare the eligibility requirements",
} as const;

export const LANDING_SCHEMES: RawSchemeData[] = [
  {
    scheme_id: "household-essentials-support",
    scheme: "Household Essentials Support",
    agency: "Community Support Office",
    scheme_type: ["Financial Assistance"],
    summary: "Short-term help with essential household expenses.",
    link: "https://example.test/household-support",
  },
  {
    scheme_id: "family-care-grant",
    scheme: "Family Care Grant",
    agency: "Family Assistance Board",
    scheme_type: ["Family & Children"],
    summary: "Support for families managing everyday care costs.",
    link: "https://example.test/family-care",
  },
];

function encodeJwtPart(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

export const E2E_AUTH_TOKEN = [
  encodeJwtPart({ alg: "none", typ: "JWT" }),
  encodeJwtPart({
    aud: E2E_FIREBASE_CONFIG.projectId,
    auth_time: 1_893_456_000,
    exp: 4_102_444_800,
    firebase: { sign_in_provider: "anonymous" },
    iat: 1_893_456_000,
    iss: `https://securetoken.google.com/${E2E_FIREBASE_CONFIG.projectId}`,
    sub: "e2e-anonymous-user",
    user_id: "e2e-anonymous-user",
  }),
  "e2e-signature",
].join(".");

const sseEvents = [
  {
    type: "status",
    data: { phase: "session_started", sessionID: "e2e-session" },
  },
  {
    type: "action_message",
    data: {
      label: "Matching support schemes",
      message: "Compared trusted schemes with the stated household need.",
    },
  },
  {
    type: "text",
    data: {
      blockIndex: 0,
      chunk: "I found two Singapore support schemes ",
    },
  },
  {
    type: "text",
    data: {
      blockIndex: 0,
      chunk: "that may help with essential household costs.",
    },
  },
  {
    type: "schemes_update",
    data: { schemes: LANDING_SCHEMES },
  },
  {
    type: "followups",
    data: { items: { [FOLLOW_UP.label]: FOLLOW_UP.value } },
  },
  { type: "done", data: {} },
];

const LANDING_RESULTS_SSE = sseEvents
  .map((event) => `data: ${JSON.stringify(event)}\n\n`)
  .join("");

type AuthRequest = {
  apiKey: string | null;
  method: string;
  operation: "lookup" | "signUp";
};

type ChatRequest = {
  authorization: string | undefined;
  body: unknown;
  method: string;
};

export type LandingResultsNetwork = {
  authRequests: AuthRequest[];
  chatRequests: ChatRequest[];
};

function isAuthEndpoint(url: URL): boolean {
  return (
    url.hostname === "identitytoolkit.googleapis.com" &&
    ["/v1/accounts:lookup", "/v1/accounts:signUp"].includes(url.pathname)
  );
}

function isChatEndpoint(url: URL): boolean {
  return (
    url.origin === E2E_API_ORIGIN &&
    url.pathname === "/agent_chat_message"
  );
}

function corsHeaders(request: Request): Record<string, string> {
  const requestedHeaders =
    request.headers()["access-control-request-headers"] ??
    "authorization, content-type";

  return {
    "access-control-allow-headers": requestedHeaders,
    "access-control-allow-methods": "POST, OPTIONS",
    "access-control-allow-origin": "*",
  };
}

export async function interceptLandingResultsJourney(
  page: Page,
): Promise<LandingResultsNetwork> {
  const network: LandingResultsNetwork = {
    authRequests: [],
    chatRequests: [],
  };

  await page.route(
    (url) =>
      ["http:", "https:"].includes(url.protocol) &&
      !["127.0.0.1", "localhost"].includes(url.hostname) &&
      !isAuthEndpoint(url) &&
      !isChatEndpoint(url),
    async (route) => {
      await route.abort("blockedbyclient");
    },
  );

  await page.route(isAuthEndpoint, async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders(request) });
      return;
    }

    const url = new URL(request.url());
    const operation = url.pathname.endsWith(":lookup") ? "lookup" : "signUp";
    network.authRequests.push({
      apiKey: url.searchParams.get("key"),
      method: request.method(),
      operation,
    });

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: corsHeaders(request),
      body: JSON.stringify(
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
    });
  });

  await page.route(isChatEndpoint, async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders(request) });
      return;
    }

    network.chatRequests.push({
      authorization: request.headers().authorization,
      body: request.postDataJSON(),
      method: request.method(),
    });

    await route.fulfill({
      status: 200,
      headers: {
        ...corsHeaders(request),
        "cache-control": "no-cache",
        "content-type": "text/event-stream; charset=utf-8",
      },
      body: LANDING_RESULTS_SSE,
    });
  });

  return network;
}
