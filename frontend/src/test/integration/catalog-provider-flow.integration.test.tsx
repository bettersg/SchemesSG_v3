import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";
import CatalogPageClient from "@/components/catalog/catalog-detail";
import { AppProviders } from "@/providers";
import { useLanguage } from "@/lib/landing-i18n";
import { catalogScheme } from "@/test/fixtures/catalog";
import { TEST_API_URL } from "@/test/mocks/handlers";
import { server } from "@/test/mocks/server";

const searchParams = vi.hoisted(() => ({
  current: null as URLSearchParams | null,
}));

vi.mock("next/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/navigation")>()),
  useSearchParams: () => searchParams.current,
}));

afterEach(() => {
  searchParams.current = null;
});

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

  it("refetches with the extra categories and areas in the query string", async () => {
    searchParams.current = new URLSearchParams(
      "category=Education&area=BEDOK&area=TOA%20PAYOH",
    );
    const requested: URL[] = [];
    server.use(
      http.get(`${TEST_API_URL}/catalog`, ({ request }) => {
        requested.push(new URL(request.url));
        return HttpResponse.json({
          data: [catalogScheme],
          total_count: 1,
          has_more: false,
        });
      }),
    );

    render(
      <AppProviders>
        <CatalogPageClient
          initialCategory="Financial Assistance"
          initialData={{ schemes: [], nextCursor: "", total: 0 }}
        />
      </AppProviders>,
    );

    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: /Financial Assistance, Education in Bedok, Toa Payoh/,
      }),
    ).toBeVisible();
    expect(
      await screen.findByRole("link", {
        name: "Test Support Scheme, Community Support Agency (opens in new tab)",
      }),
    ).toBeVisible();
    const last = requested.at(-1)!;
    expect(last.searchParams.getAll("category")).toEqual([
      "financial assistance",
      "education",
    ]);
    expect(last.searchParams.getAll("area")).toEqual(["BEDOK", "TOA PAYOH"]);
  });

  it("names the selected category in the visitor's language", async () => {
    function LanguageButtons() {
      const { setLocale } = useLanguage();
      return (
        <>
          <button onClick={() => setLocale("zh")}>zh</button>
          <button onClick={() => setLocale("en")}>en</button>
        </>
      );
    }
    render(
      <AppProviders>
        <LanguageButtons />
        <CatalogPageClient
          initialCategory="Education"
          initialData={{ schemes: [], nextCursor: "", total: 0 }}
        />
      </AppProviders>,
    );

    fireEvent.click(screen.getByRole("button", { name: "zh" }));
    try {
      expect(
        await screen.findByRole(
          "heading",
          { level: 1, name: /教育/ },
          { timeout: 5000 },
        ),
      ).toBeVisible();
    } finally {
      // The saved locale is module state; leave English for other tests.
      fireEvent.click(screen.getByRole("button", { name: "en" }));
    }
  });
});
