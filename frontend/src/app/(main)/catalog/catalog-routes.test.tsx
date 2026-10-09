import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { makeScheme } from "@/test/fixtures/scheme";
import { AppProviders } from "@/providers";

const serverMocks = vi.hoisted(() => ({
  getCatalogData: vi.fn(),
  isPublicApiConfigured: vi.fn(() => true),
}));

vi.mock("@/lib/schemes.server", () => serverMocks);

const navigationMocks = vi.hoisted(() => ({
  notFound: vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
}));

vi.mock("next/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/navigation")>()),
  notFound: navigationMocks.notFound,
}));

import CatalogPage from "./page";
import CatalogCategoryPage, { generateStaticParams } from "./[category]/page";

const schemes = [
  makeScheme({
    schemeId: "rent-relief",
    schemeName: "Rent Relief",
    agency: "Housing Board",
  }),
  makeScheme({
    schemeId: "school-meals",
    schemeName: "School Meals",
    agency: "Education Office",
  }),
];

describe("catalog routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    serverMocks.isPublicApiConfigured.mockReturnValue(true);
    serverMocks.getCatalogData.mockResolvedValue({
      schemes,
      total: schemes.length,
      nextCursor: "",
    });
  });

  it("serves /catalog as the unfiltered results, with schemes on arrival", async () => {
    render(<AppProviders>{await CatalogPage()}</AppProviders>);

    expect(serverMocks.getCatalogData).toHaveBeenCalledWith("All");
    expect(
      screen.getByRole("heading", { level: 1, name: /All schemes/ }),
    ).toBeVisible();
    // Both cards come from the server read, so nothing waits on a client fetch.
    expect(
      screen.getByRole("link", {
        name: "Rent Relief, Housing Board (opens in new tab)",
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("link", {
        name: "School Meals, Education Office (opens in new tab)",
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Browse by category" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "Explore our schemes collection" }),
    ).toBeNull();
  });

  it("leaves the unfiltered view out of the category routes", () => {
    const slugs = generateStaticParams().map(({ category }) => category);

    expect(slugs).not.toContain("all");
    expect(slugs).toContain("financial-assistance");
  });

  it("treats /catalog/all as missing, so only the redirect reaches it", async () => {
    await expect(
      CatalogCategoryPage({ params: Promise.resolve({ category: "all" }) }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    expect(serverMocks.getCatalogData).not.toHaveBeenCalled();
  });
});
