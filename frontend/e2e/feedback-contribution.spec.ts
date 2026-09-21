import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import {
  CHAT_FEEDBACK,
  CONTRIBUTION,
  SCHEME_FEEDBACK,
  interceptFeedbackContributionJourney,
} from "./fixtures/feedback-contribution";
import {
  E2E_AUTH_TOKEN,
  E2E_FIREBASE_CONFIG,
} from "./fixtures/landing-results";

test("user can submit contextual feedback and recover from an API failure", async ({
  page,
}) => {
  const network = await interceptFeedbackContributionJourney(page, {
    feedback: [
      { status: 200, body: { success: true } },
      {
        status: 503,
        body: { success: false, message: "Feedback service unavailable" },
      },
    ],
  });

  await page.goto(SCHEME_FEEDBACK.path);
  await expect(page.getByText(SCHEME_FEEDBACK.contextLabel)).toBeVisible();
  const name = page.getByRole("textbox", { name: "Name" });
  const email = page.getByRole("textbox", { name: "Email" });
  const feedback = page.getByRole("textbox", { name: "Your feedback" });
  await expect(feedback).toHaveValue(SCHEME_FEEDBACK.draft);

  await page.getByRole("button", { name: "Submit Feedback" }).click();
  await expect(name).toBeFocused();
  expect(network.submissions).toEqual([]);

  await name.fill("Aisha");
  await email.fill("aisha@example.com");
  await feedback.fill(`${SCHEME_FEEDBACK.draft}${SCHEME_FEEDBACK.detail}`);
  await page.getByRole("button", { name: "Submit Feedback" }).click();
  await expect(page.getByRole("status")).toHaveText(
    "Thank you for your feedback!",
  );
  await expect.poll(() => network.submissions.length).toBe(1);

  await page.goto(CHAT_FEEDBACK.path);
  await expect(page.getByText(CHAT_FEEDBACK.contextLabel)).toBeVisible();
  await page.getByRole("textbox", { name: "Name" }).fill("Ben");
  await page
    .getByRole("textbox", { name: "Email" })
    .fill("ben@example.com");
  const chatFeedback = page.getByRole("textbox", { name: "Your feedback" });
  await expect(chatFeedback).toHaveValue(CHAT_FEEDBACK.draft);
  await chatFeedback.fill(`${CHAT_FEEDBACK.draft}${CHAT_FEEDBACK.detail}`);
  await page.getByRole("button", { name: "Submit Feedback" }).click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Feedback service unavailable" }),
  ).toHaveText("Feedback service unavailable");
  await expect.poll(() => network.submissions.length).toBe(2);

  expect(network.submissions).toEqual([
    {
      endpoint: "feedback",
      authorization: `Bearer ${E2E_AUTH_TOKEN}`,
      body: {
        feedbackText: `${SCHEME_FEEDBACK.draft}${SCHEME_FEEDBACK.detail}`,
        userName: "Aisha",
        userEmail: "aisha@example.com",
      },
      method: "POST",
    },
    {
      endpoint: "feedback",
      authorization: `Bearer ${E2E_AUTH_TOKEN}`,
      body: {
        feedbackText: `${CHAT_FEEDBACK.draft}${CHAT_FEEDBACK.detail}`,
        userName: "Ben",
        userEmail: "ben@example.com",
      },
      method: "POST",
    },
  ]);
  expect(network.authRequests.length).toBeGreaterThan(0);
  expect(
    network.authRequests.every(
      (request) => request.apiKey === E2E_FIREBASE_CONFIG.apiKey,
    ),
  ).toBe(true);

  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);
});

test("user can validate and submit a new scheme contribution", async ({
  page,
}) => {
  const network = await interceptFeedbackContributionJourney(page);

  await page.goto("/contribute");
  const schemeName = page.getByRole("textbox", { name: "Scheme name" });
  const schemeLink = page.getByRole("textbox", { name: "Scheme link" });
  const submit = page.getByRole("button", { name: "Submit Scheme" });

  await submit.click();
  await expect(schemeName).toBeFocused();
  expect(network.submissions).toEqual([]);

  await schemeName.fill(CONTRIBUTION.scheme);
  await schemeLink.fill(CONTRIBUTION.invalidLink);
  await submit.click();
  await expect(
    page
      .getByRole("alert")
      .filter({ hasText: "Please enter a valid URL" }),
  ).toHaveText("Please enter a valid URL (e.g., https://example.com).");
  expect(network.submissions).toEqual([]);

  await schemeLink.fill(CONTRIBUTION.link);
  await submit.click();
  await expect(page.getByRole("status")).toContainText(
    "Thank you! Your submission has been received.",
  );
  await expect.poll(() => network.submissions.length).toBe(1);
  expect(network.submissions[0]).toEqual({
    endpoint: "update_scheme",
    authorization: `Bearer ${E2E_AUTH_TOKEN}`,
    body: {
      typeOfRequest: "New",
      Scheme: CONTRIBUTION.scheme,
      Link: CONTRIBUTION.link,
    },
    method: "POST",
  });
  expect(network.authRequests.length).toBeGreaterThan(0);
  expect(
    network.authRequests.every(
      (request) => request.apiKey === E2E_FIREBASE_CONFIG.apiKey,
    ),
  ).toBe(true);

  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);
});
