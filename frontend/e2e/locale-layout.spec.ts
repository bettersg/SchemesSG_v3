import { expect, test } from "@playwright/test";
import {
  LANDING_QUERY,
  interceptLandingResultsJourney,
  waitForHydration,
} from "./fixtures/landing-results";

// Translations run much longer than English (the Tamil navbar tabs need over
// twice the width), so every language is checked at phone and desktop widths
// rather than trusting a layout tuned in English.
//
// The PR lane shares a 120s budget across all e2e specs, so it checks one
// phone and one desktop width on the densest pages. The nightly Chromium run
// sets LOCALE_LAYOUT_FULL=1 for every width and page.
const FULL = process.env.LOCALE_LAYOUT_FULL === "1";
const LOCALES = ["en", "zh", "ta", "ms"] as const;
const WIDTHS = FULL ? [320, 390, 1024, 1280] : [390, 1280];
const PAGES = FULL
  ? [
      "/",
      "/about",
      "/contribute",
      "/catalog",
      "/schemes/family-care-fund",
      "/schemes/bright-start-support",
    ]
  : ["/", "/catalog", "/schemes/bright-start-support"];

for (const locale of LOCALES) {
  test(`${locale}: pages fit the screen and the navbar never overlaps`, async ({
    page,
  }) => {
    test.setTimeout(120_000);
    await page.addInitScript((saved) => {
      localStorage.setItem("schemes-lang", saved);
    }, locale);

    for (const width of WIDTHS) {
      await page.setViewportSize({ width, height: 800 });
      for (const path of PAGES) {
        await page.goto(path);
        await expect(page.locator("html")).toHaveAttribute(
          "lang",
          locale === "zh" ? "zh-Hans" : locale,
        );
        await page.evaluate(() => document.fonts.ready);

        const layout = await page.evaluate(() => {
          window.scrollTo(10_000, 0);
          const scrolledSideways = window.scrollX;
          window.scrollTo(0, 0);
          const nav = document.querySelector("header nav");
          const tabs = nav?.querySelector('[role="tablist"]');
          const shown =
            tabs && tabs.closest('[aria-hidden="true"]') === null
              ? tabs.getBoundingClientRect()
              : null;
          const language = nav?.querySelector('button[aria-haspopup]');
          const languageBox =
            language && (language as HTMLElement).offsetParent
              ? language.getBoundingClientRect()
              : null;
          // Fixed bars do not widen the page, so text spilling out of a button
          // or link has to be caught on the control itself. scrollWidth rounds
          // up and clientWidth down, so glyph ink alone reads 2px over.
          const clipped = [...document.querySelectorAll("button, a")]
            .filter(
              (el) =>
                (el as HTMLElement).offsetParent !== null &&
                el.scrollWidth > el.clientWidth + 4,
            )
            .map((el) => (el.textContent ?? "").trim().slice(0, 40));
          // Rows of tabs or links that run past their own box without a scroll
          // container (the navbar keeps its hidden tabs out of the check).
          const spilled = [...document.querySelectorAll("nav *")]
            .filter((el) => {
              if (el.closest('[aria-hidden="true"]')) return false;
              if ((el as HTMLElement).offsetParent === null) return false;
              const overflowX = getComputedStyle(el).overflowX;
              return (
                overflowX === "visible" && el.scrollWidth > el.clientWidth + 4
              );
            })
            .map((el) => (el.textContent ?? "").trim().slice(0, 40));
          return {
            clipped,
            spilled,
            scrolledSideways,
            tabsRight: shown && shown.width > 0 ? shown.right : null,
            languageLeft: languageBox?.left ?? null,
          };
        });

        const where = `${path} at ${width}px`;
        expect(layout.scrolledSideways, `${where} scrolls sideways`).toBe(0);
        expect(layout.clipped, `${where}: text spills out of a control`).toEqual(
          [],
        );
        expect(layout.spilled, `${where}: a row runs past its box`).toEqual(
          [],
        );
        if (layout.tabsRight !== null && layout.languageLeft !== null) {
          expect(
            layout.tabsRight,
            `${where}: navbar tabs run into the language menu`,
          ).toBeLessThanOrEqual(layout.languageLeft);
        }
      }
    }
  });
}

// A started chat has its own phone toolbar (chat and schemes tabs, New chat)
// and a results header, neither of which exists before the first search.
const CHAT_LOCALES = FULL ? LOCALES : (["zh", "ta"] as const);
const CHAT_WIDTHS = FULL ? [320, 390] : [320];

for (const locale of CHAT_LOCALES) {
  test(`${locale}: the phone chat toolbar and results header fit the screen`, async ({
    page,
  }) => {
    test.setTimeout(90_000);
    await interceptLandingResultsJourney(page);
    await page.addInitScript((saved) => {
      localStorage.setItem("schemes-lang", saved);
    }, locale);

    for (const width of CHAT_WIDTHS) {
      await page.setViewportSize({ width, height: 800 });
      await page.goto("/");
      await waitForHydration(page.getByRole("textbox"));
      await page.getByRole("textbox").fill(LANDING_QUERY);
      await page.getByRole("textbox").press("Enter");

      const tabs = page.getByRole("tab").filter({ visible: true });
      await expect(tabs).toHaveCount(2);
      await tabs.nth(1).click();
      await expect(
        page.locator('a[href^="/schemes/"]').filter({ visible: true }).first(),
      ).toBeVisible();

      const overflowing = await page.evaluate(() => {
        // Screen-reader-only text is a 1px box that always measures as
        // overflowing, so it is taken out of the layout before measuring.
        document
          .querySelectorAll<HTMLElement>(".sr-only")
          .forEach((el) => (el.style.display = "none"));
        const toolbars = [...document.querySelectorAll('[role="tablist"]')]
          .filter((list) => !list.closest("header"))
          .map((list) => list.parentElement);
        const rows = [
          ...toolbars,
          ...document.querySelectorAll('[role="status"]'),
        ].filter((el): el is HTMLElement => !!el && el.offsetParent !== null);
        if (rows.length === 0) return ["no chat toolbar or results header found"];
        return rows
          .flatMap((row) => [row, ...row.querySelectorAll<HTMLElement>("*")])
          .filter((el) => el.offsetParent !== null)
          .filter((el) => el.getBoundingClientRect().right > window.innerWidth + 1)
          .map((el) => (el.textContent ?? "").trim().slice(0, 40));
      });
      expect(overflowing, `chat at ${width}px runs off the screen`).toEqual([]);
    }
  });
}
