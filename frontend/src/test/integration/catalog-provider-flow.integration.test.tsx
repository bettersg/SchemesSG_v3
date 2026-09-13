import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CatalogPageClient from "@/components/catalog/catalog-detail";
import { AppProviders } from "@/providers";

describe("catalog provider flow", () => {
  it("shows catalog results after public API loading", async () => {
    render(
      <AppProviders>
        <CatalogPageClient initialCategory="Financial Assistance" />
      </AppProviders>,
    );

    expect(
      await screen.findByRole("link", {
        name: "Test Support Scheme, Community Support Agency (opens in new tab)",
      }),
    ).toBeVisible();
  });
});
