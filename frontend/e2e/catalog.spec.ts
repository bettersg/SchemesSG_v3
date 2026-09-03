import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "next/experimental/testmode/playwright";
import path from "node:path";
import {
  CATALOG_SCHEMES,
  interceptCatalogSchemeJourney,
} from "./fixtures/catalog-scheme";

test("user can choose a catalog category and see matching schemes", async ({
  page,
}) => {
  test.setTimeout(60_000);
  const network = await interceptCatalogSchemeJourney(page, {
    holdInitialCatalog: true,
  });
  await page.goto("/catalog");

  await expect(
    page.getByRole("heading", { name: "Explore our schemes collection" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Financial Assistance" }).click();
  try {
    await expect(page.getByLabel("Loading schemes")).toBeVisible({
      timeout: 20_000,
    });
  } finally {
    network.releaseInitialCatalog();
  }

  const firstScheme = page.getByRole("link", {
    name: `${CATALOG_SCHEMES[0].scheme}, ${CATALOG_SCHEMES[0].agency} (opens in new tab)`,
  });
  await expect(firstScheme).toBeVisible();
  await expect(page.getByText("(3)", { exact: true })).toBeVisible();
  const accessibilityScan = await new AxeBuilder({ page })
    .include("main")
    .analyze();
  expect(accessibilityScan.violations).toEqual([]);
  await page.mouse.move(1200, 750);
  await expect(page.locator("main")).toHaveScreenshot("catalog-grid.png", {
    animations: "disabled",
    caret: "hide",
    scale: "css",
    stylePath: path.join(__dirname, "fixtures/visual-baseline.css"),
  });
  expect(network.catalogRequests).toEqual(
    expect.arrayContaining([
      {
        authorization: expect.stringMatching(/^Bearer /),
        category: "financial assistance",
        limit: "20",
        method: "GET",
      },
    ]),
  );

  await page.getByRole("link", { name: "Education", exact: true }).click();
  await expect(page.getByText("No schemes found", { exact: true })).toBeVisible();
  await expect(page.getByText("(0)", { exact: true })).toBeVisible();
});
