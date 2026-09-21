import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import path from "node:path";
import {
  LANDING_ANSWER,
  LANDING_QUERY,
  LANDING_SCHEMES,
  interceptLandingResultsJourney,
} from "./fixtures/landing-results";

test("mobile navigation and chat result tabs remain usable", async ({ page }) => {
  await interceptLandingResultsJourney(page);
  await page.goto("/");

  const header = page.getByRole("banner");
  await header.getByRole("button", { name: "Open menu" }).click();
  for (const linkName of ["Catalog", "Contribute", "About"]) {
    await expect(header.getByRole("link", { name: linkName })).toBeVisible();
  }
  await header.getByRole("button", { name: "Close menu" }).click();

  await page.getByRole("textbox").fill(LANDING_QUERY);
  await page.getByRole("button", { name: "Search", exact: true }).click();

  const chatTab = page.getByRole("tab", { name: "Chat" });
  const schemesTab = page.getByRole("tab", { name: "Schemes" });
  const schemeUpdateNotice = page.getByRole("button", {
    name: "2 schemes found",
  });
  await expect(chatTab).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();

  await schemeUpdateNotice.click();
  await expect(schemesTab).toHaveAttribute("aria-selected", "true");
  for (const scheme of LANDING_SCHEMES) {
    await expect(
      page.getByRole("link", {
        name: `${scheme.scheme}, ${scheme.agency} (opens in new tab)`,
      }),
    ).toBeVisible();
  }

  await chatTab.click();
  await expect(chatTab).toHaveAttribute("aria-selected", "true");
  await expect(
    page.getByText(LANDING_ANSWER, { exact: true }).filter({ visible: true }),
  ).toBeVisible();
  await expect(schemeUpdateNotice.locator("..")).toHaveCSS("opacity", "1");
  await expect(schemesTab).toHaveAccessibleName(/^Schemes$/);
  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);
  await expect(
    page
      .getByText("Anonymous · No personal data stored", { exact: true })
      .filter({ visible: true }),
  ).toBeInViewport({ ratio: 1 });
  await expect(page.locator("main")).toHaveScreenshot("mobile-chat.png", {
    animations: "disabled",
    caret: "hide",
    scale: "css",
    stylePath: path.join(__dirname, "fixtures/visual-baseline.css"),
  });
});
