import { act, render, screen, waitFor } from "@testing-library/react";
import { Trans } from "@lingui/react/macro";
import { afterEach, describe, expect, it } from "vitest";
import { LanguageProvider, useLanguage } from "./LanguageContext";
import { i18n } from "@/i18n/lingui";

const CHINESE_FACE = 'link[href="/fonts/noto-sans-sc/noto-sans-sc.css"]';

function Probe() {
  const { setLocale } = useLanguage();
  return (
    <>
      <p>
        <Trans>Catalogue</Trans>
      </p>
      <p>
        <Trans>Message with no Chinese translation</Trans>
      </p>
      <button onClick={() => setLocale("zh")}>zh</button>
      <button onClick={() => setLocale("en")}>en</button>
      <button onClick={() => setLocale("ta")}>ta</button>
      <button onClick={() => setLocale("ms")}>ms</button>
    </>
  );
}

describe("LanguageProvider with Lingui", () => {
  afterEach(() => {
    act(() => screen.queryByRole("button", { name: "en" })?.click());
  });

  it("renders English by default", () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );
    expect(screen.getByText("Catalogue")).toBeVisible();
    expect(i18n.locale).toBe("en");
    expect(document.querySelectorAll(CHINESE_FACE)).toHaveLength(0);
  });

  it("switches to Chinese without a reload and falls back to English", async () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    act(() => screen.getByRole("button", { name: "zh" }).click());

    expect(await screen.findByText("目录")).toBeVisible();
    expect(
      screen.getByText("Message with no Chinese translation"),
    ).toBeVisible();
    expect(document.documentElement.lang).toBe("zh-Hans");
    expect(document.querySelectorAll(CHINESE_FACE)).toHaveLength(1);
  });

  it("switches to Tamil and sets lang attribute", async () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    act(() => screen.getByRole("button", { name: "ta" }).click());

    expect(await screen.findByText("Catalogue")).toBeVisible();
    expect(document.documentElement.lang).toBe("ta");
    await waitFor(() => expect(i18n.locale).toBe("ta"));
  });

  it("switches to Malay and sets lang attribute", async () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    act(() => screen.getByRole("button", { name: "ms" }).click());

    expect(await screen.findByText("Catalogue")).toBeVisible();
    expect(document.documentElement.lang).toBe("ms");
    await waitFor(() => expect(i18n.locale).toBe("ms"));
  });

  it("follows a language change made in another tab", async () => {
    render(
      <LanguageProvider>
        <Probe />
      </LanguageProvider>,
    );

    // Another tab saves the choice; this tab only hears the storage event.
    act(() => {
      localStorage.setItem("schemes-lang", "zh");
      window.dispatchEvent(
        new StorageEvent("storage", { key: "schemes-lang", newValue: "zh" }),
      );
    });

    expect(await screen.findByText("目录")).toBeVisible();
    expect(document.documentElement.lang).toBe("zh-Hans");
  });
});
