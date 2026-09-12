import { expect, test } from "@playwright/test";
import {
  CATALOG_SCHEMES,
  EXTERNAL_SCHEME_URL,
  SCHEME_DETAIL,
  SCHEME_DETAIL_ID,
  interceptCatalogSchemeJourney,
  interceptSchemeDetailJourney,
} from "./fixtures/catalog-scheme";

test("user can open a catalog scheme and continue to its official website", async ({
  context,
  page,
}) => {
  const network = await interceptCatalogSchemeJourney(page);
  await interceptSchemeDetailJourney(context);
  await page.goto("/catalog");
  await page.getByRole("link", { name: "Financial Assistance" }).click();

  const schemeLink = page.getByRole("link", {
    name: `${CATALOG_SCHEMES[0].scheme}, ${CATALOG_SCHEMES[0].agency} (opens in new tab)`,
  });
  await expect(schemeLink).toHaveAttribute(
    "href",
    `/schemes/${SCHEME_DETAIL_ID}`,
  );
  await expect(schemeLink).toHaveAttribute("target", "_blank");

  const schemePopupPromise = page.waitForEvent("popup");
  await schemeLink.click();
  const schemePage = await schemePopupPromise;

  await expect(schemePage).toHaveURL(`/schemes/${SCHEME_DETAIL_ID}`);
  await expect(
    schemePage.getByRole("heading", { name: SCHEME_DETAIL.scheme }),
  ).toBeVisible();
  await expect(schemePage.getByText(SCHEME_DETAIL.summary!)).toBeVisible();
  await expect(
    schemePage.getByRole("heading", { name: "Who qualifies" }),
  ).toBeVisible();
  await expect(
    schemePage.getByRole("heading", { name: "How to apply" }),
  ).toBeVisible();

  const externalPopupPromise = schemePage.waitForEvent("popup");
  await schemePage.getByRole("link", { name: "Visit website" }).click();
  const externalPage = await externalPopupPromise;
  await expect(externalPage).toHaveURL(EXTERNAL_SCHEME_URL);
  await expect(
    externalPage.getByRole("heading", { name: "Bright Start application" }),
  ).toBeVisible();

  // The detail route is a public build-time read: it must reach the API
  // anonymously, exactly like the static export does.
  const schemeRequests = (await network.readPublicFixtureRequests()).filter(
    (request) => request.resource === "scheme",
  );
  expect(schemeRequests).toEqual(
    expect.arrayContaining([
      {
        resource: "scheme",
        authorization: null,
        method: "GET",
        schemeId: SCHEME_DETAIL_ID,
      },
    ]),
  );
});
