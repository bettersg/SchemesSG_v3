import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "next/experimental/testmode/playwright";
import path from "node:path";
import {
  SCHEME_DETAIL,
  SCHEME_DETAIL_ID,
  interceptSchemeDetailJourney,
} from "./fixtures/catalog-scheme";

test("mobile scheme details remain accessible and actionable", async ({
  context,
  next,
  page,
}) => {
  await interceptSchemeDetailJourney(next, context);
  await page.goto(`/schemes/${SCHEME_DETAIL_ID}`);

  await expect(
    page.getByRole("heading", { name: SCHEME_DETAIL.scheme }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Who qualifies" }),
  ).toBeVisible();
  const visitWebsite = page.getByRole("link", { name: "Visit website" });
  await expect(visitWebsite).toBeVisible();
  await expect(visitWebsite).toBeInViewport({ ratio: 1 });

  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);
  await expect(page.locator("main")).toHaveScreenshot(
    "mobile-scheme-detail.png",
    {
      animations: "disabled",
      caret: "hide",
      scale: "css",
      stylePath: path.join(__dirname, "fixtures/visual-baseline.css"),
    },
  );

  await page.getByRole("link", { name: "How to apply" }).click();
  await expect(page).toHaveURL(/#how-to-apply$/);
  await expect(
    page.getByRole("heading", { name: "How to apply" }),
  ).toBeInViewport();
});
