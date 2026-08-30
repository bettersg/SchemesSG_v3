import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import {
  CANCELLED_STREAM_TEXT,
  CANCELLATION_QUERY,
  FAILED_STREAM_TEXT,
  FAILURE_QUERY,
  RECOVERY_ANSWER,
  completedLandingScenario,
  interceptChatStreamScenarios,
} from "./fixtures/chat-resilience";
import {
  LANDING_ANSWER,
  LANDING_QUERY,
  LANDING_SCHEMES,
} from "./fixtures/landing-results";

test("user can stop a streaming response with the question ready to retry", async ({
  page,
}) => {
  await interceptChatStreamScenarios(page, [
    {
      events: [
        {
          type: "text",
          data: { blockIndex: 0, chunk: CANCELLED_STREAM_TEXT },
        },
      ],
      finish: "hold",
    },
  ]);

  await page.goto("/");
  await page.getByRole("textbox").fill(CANCELLATION_QUERY);
  await page.getByRole("button", { name: "Search" }).click();

  const partialAnswer = page
    .getByText(CANCELLED_STREAM_TEXT)
    .filter({ visible: true });
  await expect(partialAnswer).toBeVisible();
  await page.getByRole("button", { name: "Stop generating" }).click();

  await expect(partialAnswer).toBeHidden();
  await expect(page.getByRole("textbox")).toHaveValue(CANCELLATION_QUERY);
  await expect(page.getByRole("button", { name: "Search" })).toBeEnabled();
  await expect(page.getByText("Unable to finish response")).toHaveCount(0);
});

test("user can recover from a failed stream without losing prior results", async ({
  page,
}) => {
  const streams = await interceptChatStreamScenarios(page, [
    completedLandingScenario,
    {
      events: [
        {
          type: "text",
          data: { blockIndex: 0, chunk: FAILED_STREAM_TEXT },
        },
      ],
      finish: "controlled-error",
    },
    {
      events: [
        {
          type: "text",
          data: { blockIndex: 0, chunk: RECOVERY_ANSWER },
        },
        { type: "done", data: {} },
      ],
      finish: "complete",
    },
  ]);

  await page.goto("/");
  await page.getByRole("textbox").fill(LANDING_QUERY);
  await page.getByRole("button", { name: "Search" }).click();
  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();

  await page.getByRole("textbox").fill(FAILURE_QUERY);
  await page.getByRole("button", { name: "Send message" }).click();
  const failedPartialAnswer = page
    .getByText(FAILED_STREAM_TEXT, { exact: true })
    .filter({ visible: true });
  await expect(failedPartialAnswer).toBeVisible();
  await streams.failActive();

  await expect(
    page.getByRole("alert").filter({ hasText: "Unable to finish response" }),
  ).toContainText("Send it again when ready");
  await expect(failedPartialAnswer).toBeHidden();
  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toHaveText("2 schemes found");
  for (const scheme of LANDING_SCHEMES) {
    await expect(
      page.getByRole("link", {
        name: `${scheme.scheme}, ${scheme.agency} (opens in new tab)`,
      }),
    ).toBeVisible();
  }
  await expect(page.getByRole("textbox")).toHaveValue(FAILURE_QUERY);
  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);

  await page.getByRole("button", { name: "Send message" }).click();
  await expect(
    page.getByText(RECOVERY_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
  await expect(page.getByText("Unable to finish response")).toHaveCount(0);
  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
});
