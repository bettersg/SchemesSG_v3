import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import path from "node:path";
import {
  CATALOG_SCHEMES,
  interceptCatalogSchemeJourney,
} from "./fixtures/catalog-scheme";

const publicCatalogRead = {
  resource: "catalog",
  authorization: null,
  initiator: "server",
  cursor: null,
  limit: "20",
  method: "GET",
} as const;

test("user sees schemes on arrival and narrows them by category", async ({
  page,
}) => {
  test.setTimeout(60_000);
  const network = await interceptCatalogSchemeJourney(page);
  const firstScheme = page.getByRole("link", {
    name: `${CATALOG_SCHEMES[0].scheme}, ${CATALOG_SCHEMES[0].agency} (opens in new tab)`,
  });

  await page.goto("/catalog");

  // Schemes are on screen straight away, with no category to choose first.
  await expect(
    page.getByRole("heading", { level: 1, name: /All schemes/ }),
  ).toBeVisible();
  await expect(firstScheme).toBeVisible();
  await expect(page.getByText("(4)", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Browse by category" }).click();
  await page
    .getByRole("dialog")
    .getByRole("link", { name: "Financial Assistance" })
    .click();
  // `next dev` compiles `/catalog/[category]` on the first navigation to it, and
  // the router holds the URL until that payload arrives.
  await expect(page).toHaveURL("/catalog/financial-assistance", {
    timeout: 20_000,
  });
  await expect(
    page.getByRole("heading", { level: 1, name: /Financial Assistance/ }),
  ).toBeVisible();
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

  // Each route reads its own first page on the server, anonymously and exactly
  // once. A "browser" entry here would be a page refetching after hydration.
  const catalogRequests = (await network.readPublicFixtureRequests()).filter(
    (request) => request.resource === "catalog",
  );
  expect(catalogRequests).toEqual([
    { ...publicCatalogRead, category: null },
    { ...publicCatalogRead, category: "Financial Assistance" },
  ]);

  await page.goto("/catalog/education");
  await expect(
    page.getByText("No schemes found", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("(0)", { exact: true })).toBeVisible();
});

test("an old /catalog/all link lands on the unfiltered catalog", async ({
  page,
  request,
}) => {
  // Permanent, so search engines move the old URL's standing onto /catalog.
  const redirect = await request.get("/catalog/all", { maxRedirects: 0 });
  expect(redirect.status()).toBe(308);
  expect(redirect.headers()["location"]).toBe("/catalog");

  await interceptCatalogSchemeJourney(page);
  await page.goto("/catalog/all");
  await expect(page).toHaveURL("/catalog");
  await expect(
    page.getByRole("heading", { level: 1, name: /All schemes/ }),
  ).toBeVisible();
});
