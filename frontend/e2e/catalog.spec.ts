import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import path from "node:path";
import {
  CATALOG_SCHEMES,
  interceptCatalogSchemeJourney,
} from "./fixtures/catalog-scheme";

test("user can choose a catalog category and see matching schemes", async ({
  page,
}) => {
  test.setTimeout(60_000);
  const network = await interceptCatalogSchemeJourney(page);
  await page.goto("/catalog");

  await expect(
    page.getByRole("heading", { name: "Explore our schemes collection" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Financial Assistance" }).click();
  // `next dev` compiles `/catalog/[category]` on the first navigation to it, and
  // the router holds the URL until that payload arrives.
  await expect(page).toHaveURL("/catalog/financial-assistance", {
    timeout: 20_000,
  });
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
  // The category page is server-rendered, so its public catalog read must reach
  // the API anonymously, with the shared page size, and exactly once. A
  // "browser" entry here would be the page refetching after hydration.
  const catalogRequests = (await network.readPublicFixtureRequests()).filter(
    (request) => request.resource === "catalog",
  );
  expect(catalogRequests).toEqual([
    {
      resource: "catalog",
      authorization: null,
      initiator: "server",
      category: "Financial Assistance",
      cursor: null,
      limit: "20",
      method: "GET",
    },
  ]);

  await page.goto("/catalog/education");
  await expect(
    page.getByText("No schemes found", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("(0)", { exact: true })).toBeVisible();
});
