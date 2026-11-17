import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LanguageProvider, useLanguage } from "@/lib/landing-i18n";
import { activateLocale, i18n } from "./lingui";

// Chinese arrives slowly and Malay fails, so switches can overlap or break.
vi.mock("@/locales/zh/messages", async () => {
  await new Promise((resolve) => setTimeout(resolve, 100));
  return { messages: {} };
});
vi.mock("@/locales/ms/messages", () => {
  throw new Error("chunk failed to load");
});

function Probe() {
  const { locale, setLocale } = useLanguage();
  return (
    <>
      <p>Showing {locale}</p>
      <button onClick={() => setLocale("ms")}>ms</button>
    </>
  );
}

describe("activateLocale", () => {
  afterEach(async () => {
    await activateLocale("en");
    vi.restoreAllMocks();
  });

  it("loads each catalog once", async () => {
    const load = vi.spyOn(i18n, "load");
    await activateLocale("ta");
    await activateLocale("en");
    await activateLocale("ta");

    expect(load.mock.calls.filter(([locale]) => locale === "ta")).toHaveLength(1);
    expect(i18n.locale).toBe("ta");
  });

  it("keeps the latest choice when an earlier catalog arrives later", async () => {
    const slowChinese = activateLocale("zh");
    const tamil = activateLocale("ta");
    await Promise.all([slowChinese, tamil]);

    expect(i18n.locale).toBe("ta");
  });

  it("rejects and keeps the current language when a catalog fails", async () => {
    await expect(activateLocale("ms")).rejects.toThrow();
    expect(i18n.locale).toBe("en");
  });

  it("shows the language still on screen but keeps the saved choice when a catalog fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    act(() => screen.getByRole("button", { name: "ms" }).click());

    expect(await screen.findByText("Showing en")).toBeVisible();
    expect(document.documentElement.lang).toBe("en");
    expect(i18n.locale).toBe("en");
    // A failed download is usually transient, so the next visit tries again.
    expect(localStorage.getItem("schemes-lang")).toBe("ms");
  });
});
