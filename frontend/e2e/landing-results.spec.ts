import { expect, test } from "@playwright/test";
import {
  E2E_AUTH_TOKEN,
  E2E_FIREBASE_CONFIG,
  FOLLOW_UP,
  LANDING_ANSWER,
  LANDING_QUERY,
  LANDING_SCHEMES,
  interceptLandingResultsJourney,
} from "./fixtures/landing-results";

test("user can search from the landing page and receive streamed results", async ({
  page,
}) => {
  const network = await interceptLandingResultsJourney(page);

  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Find the Right Schemes, All in One Place",
    }),
  ).toBeVisible();

  const searchInput = page.getByPlaceholder(
    "I'm a single parent looking for financial assistance...",
  );
  await searchInput.fill(LANDING_QUERY);
  await page.getByRole("button", { name: "Search" }).click();

  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "How I found these (1 step)" }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("2 schemes found");

  for (const scheme of LANDING_SCHEMES) {
    await expect(
      page.getByRole("link", {
        name: `${scheme.scheme}, ${scheme.agency} (opens in new tab)`,
      }),
    ).toBeVisible();
  }

  await expect(
    page.getByText(FOLLOW_UP.label, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
  await expect(
    page
      .getByPlaceholder("Ask a follow-up question…")
      .filter({ visible: true }),
  ).toBeEnabled();

  expect(network.authRequests).toEqual([
    {
      apiKey: E2E_FIREBASE_CONFIG.apiKey,
      method: "POST",
      operation: "signUp",
    },
    {
      apiKey: E2E_FIREBASE_CONFIG.apiKey,
      method: "POST",
      operation: "lookup",
    },
  ]);
  expect(network.chatRequests).toEqual([
    {
      authorization: `Bearer ${E2E_AUTH_TOKEN}`,
      body: { message: LANDING_QUERY },
      method: "POST",
    },
  ]);
});
