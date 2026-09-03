import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LanguageProvider } from "@/lib/landing-i18n";
import { en } from "@/lib/landing-i18n/translations/en";
import { zh } from "@/lib/landing-i18n/translations/zh";
import { FAQSection } from "./faq-section";

const apiItem = en.faq.items.find((item) => item.answerLink);

/**
 * The API answer shipped once with a bare "/developers" written into the prose,
 * so the docs page was named but not reachable. Pin the link in both languages.
 */
describe("FAQ section", () => {
  it("links the API answer to the developer docs", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <FAQSection />
      </LanguageProvider>,
    );

    // Answers live in collapsed panels, so open the one being asserted.
    await user.click(screen.getByText(apiItem!.question));

    expect(
      await screen.findByRole("link", { name: apiItem!.answerLink!.label }),
    ).toHaveAttribute("href", "/developers");
  });

  it.each([
    ["en", en],
    ["zh", zh],
  ])("names /developers in the %s API answer", (_lang, dict) => {
    const apiItem = dict.faq.items.find((item) => item.answerLink);
    expect(apiItem?.answerLink?.href).toBe("/developers");
    // The link replaced a bare path in the prose; it must not come back.
    expect(apiItem?.answer).not.toContain("/developers");
  });
});
