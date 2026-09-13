import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LanguageProvider } from "@/lib/landing-i18n";
import { Navbar } from "./navbar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/catalog",
}));

describe("Navbar", () => {
  it("opens and closes the mobile navigation with core routes available", async () => {
    const user = userEvent.setup();
    const { unmount } = render(
      <LanguageProvider>
        <Navbar />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Open menu" }));
    expect(screen.getByRole("button", { name: "Close menu" })).toBeVisible();
    expect(
      screen.getAllByRole("link", { name: "Catalog" }).length,
    ).toBeGreaterThan(1);
    expect(
      screen.getAllByRole("link", { name: "Contribute" }).length,
    ).toBeGreaterThan(1);
    expect(
      screen.getAllByRole("link", { name: "About" }).length,
    ).toBeGreaterThan(1);

    await user.click(screen.getByRole("button", { name: "Close menu" }));
    expect(screen.getByRole("button", { name: "Open menu" })).toBeVisible();
    expect(document.documentElement.dataset.mobileNavHidden).toBe("false");

    unmount();
    expect(document.documentElement.dataset.mobileNavHidden).toBeUndefined();
  });
});
