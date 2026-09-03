import { expect, test } from "@playwright/test";

const query = process.env.DEV_SMOKE_QUERY ?? "financial assistance for families";

test("development stack returns real scheme search results", async ({ page }) => {
  await page.goto("/");

  const searchInput = page.getByPlaceholder(
    "I'm a single parent looking for financial assistance...",
  );
  await searchInput.fill(query);
  await page.getByRole("button", { name: "Search" }).click();

  const resultStatus = page.getByRole("status");
  await expect(resultStatus).toHaveText(/[1-9]\d* schemes? found/, {
    timeout: 120_000,
  });
  await expect(
    page.getByRole("link", { name: /opens in new tab/ }).first(),
  ).toBeVisible();
});
