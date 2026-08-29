import { http, HttpResponse } from "msw";
import { catalogScheme } from "@/test/fixtures/catalog";

export const TEST_API_URL = "https://api.test";
export const TEST_AUTH_TOKEN = "test-auth-token";

export const handlers = [
  http.get(`${TEST_API_URL}/catalog`, ({ request }) => {
    const url = new URL(request.url);
    const isExpectedRequest =
      request.headers.get("authorization") === `Bearer ${TEST_AUTH_TOKEN}` &&
      url.searchParams.get("category") === "financial assistance" &&
      url.searchParams.get("limit") === "20";

    if (!isExpectedRequest) {
      return HttpResponse.json(
        { error: "Unexpected test request" },
        { status: 400 },
      );
    }

    return HttpResponse.json({
      data: [catalogScheme],
      total_count: 1,
      has_more: false,
    });
  }),
];
