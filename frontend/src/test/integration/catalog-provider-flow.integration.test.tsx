import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import CatalogPageClient from "@/components/catalog/catalog-detail";
import { AppProviders } from "@/providers";

vi.mock("@/lib/auth-gateway", () => ({
  getAuthToken: async () => "test-auth-token",
  observeAuthState: (listener: (user: { uid: string }) => void) => {
    listener({ uid: "test-user" });
    return () => undefined;
  },
}));

describe("catalog provider flow", () => {
  it("shows catalog results after authentication and API loading", async () => {
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
