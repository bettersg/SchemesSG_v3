import type { Page, Request } from "@playwright/test";
import {
  E2E_API_ORIGIN,
  interceptLandingResultsJourney,
} from "./landing-results";

export const SCHEME_FEEDBACK = {
  path: "/feedback?source=scheme&schemeId=child-care-subsidy&scheme=Child+Care+Subsidy",
  contextLabel: "Suggest a correction for Child Care Subsidy",
  draft:
    "Scheme correction\nScheme ID: child-care-subsidy\nScheme: Child Care Subsidy\n\n",
  detail: "The eligibility information is outdated.",
} as const;

export const CHAT_FEEDBACK = {
  path: "/feedback?source=chat",
  contextLabel: "Feedback about a chat response",
  draft: "Chat response feedback:\n\n",
  detail: "The response missed the relevant scheme.",
} as const;

export const CONTRIBUTION = {
  scheme: "Community Support Grant",
  invalidLink: "javascript:alert(1)",
  link: "https://support.example.test/grant",
} as const;

type SubmissionEndpoint = "feedback" | "update_scheme";

type MockApiResponse = {
  status: number;
  body: {
    success: boolean;
    message?: string;
  };
};

type SubmissionResponses = Partial<
  Record<SubmissionEndpoint, MockApiResponse[]>
>;

export type CapturedSubmission = {
  endpoint: SubmissionEndpoint;
  authorization: string | undefined;
  body: unknown;
  method: string;
};

const successfulResponse: MockApiResponse = {
  status: 200,
  body: { success: true },
};

function isSubmissionEndpoint(url: URL): boolean {
  return (
    url.origin === E2E_API_ORIGIN &&
    ["/feedback", "/update_scheme"].includes(url.pathname)
  );
}

function corsHeaders(request: Request): Record<string, string> {
  return {
    "access-control-allow-headers":
      request.headers()["access-control-request-headers"] ??
      "authorization, content-type",
    "access-control-allow-methods": "POST, OPTIONS",
    "access-control-allow-origin": "*",
  };
}

export async function interceptFeedbackContributionJourney(
  page: Page,
  responses: SubmissionResponses = {},
) {
  const landingNetwork = await interceptLandingResultsJourney(page);
  const submissions: CapturedSubmission[] = [];
  const responseIndexes: Record<SubmissionEndpoint, number> = {
    feedback: 0,
    update_scheme: 0,
  };

  await page.route(isSubmissionEndpoint, async (route) => {
    const request = route.request();
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders(request) });
      return;
    }

    const endpoint = new URL(request.url()).pathname.slice(
      1,
    ) as SubmissionEndpoint;
    submissions.push({
      endpoint,
      authorization: request.headers().authorization,
      body: request.postDataJSON(),
      method: request.method(),
    });

    const responseIndex = responseIndexes[endpoint];
    responseIndexes[endpoint] += 1;
    const response = responses[endpoint]?.[responseIndex] ?? successfulResponse;
    await route.fulfill({
      status: response.status,
      contentType: "application/json",
      headers: corsHeaders(request),
      body: JSON.stringify(response.body),
    });
  });

  return {
    authRequests: landingNetwork.authRequests,
    submissions,
  };
}
