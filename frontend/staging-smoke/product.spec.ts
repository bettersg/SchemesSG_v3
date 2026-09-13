import { expect, test } from "./read-only-fixture";
import { STAGING_ORIGIN } from "./read-only-network";

test("deployed staging renders the landing and catalog routes without writes", async ({
  page,
}) => {
  const landingResponse = await page.goto("/");
  expect(landingResponse?.status()).toBe(200);
  await expect(
    page.getByRole("heading", {
      name: "Find the Right Schemes, All in One Place",
    }),
  ).toBeVisible();

  await page.getByRole("link", { name: "Catalog", exact: true }).first().click();
  await expect(page).toHaveURL(`${STAGING_ORIGIN}/catalog`);
  await expect(
    page.getByRole("heading", { name: "Explore our schemes collection" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Financial Assistance" }),
  ).toBeVisible();
});
