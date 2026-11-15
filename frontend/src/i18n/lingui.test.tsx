import { act, render, screen, waitFor } from "@testing-library/react";
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
  const { setLocale } = useLanguage();
  return <button onClick={() => setLocale("ms")}>ms</button>;
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

  it("puts the saved choice and page language back when a catalog fails", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    act(() => screen.getByRole("button", { name: "ms" }).click());

    await waitFor(() => expect(localStorage.getItem("schemes-lang")).toBe("en"));
    expect(document.documentElement.lang).toBe("en");
    expect(i18n.locale).toBe("en");
  });
});
