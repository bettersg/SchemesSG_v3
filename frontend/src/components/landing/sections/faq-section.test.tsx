import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LanguageProvider, useLanguage } from "@/lib/landing-i18n";
import { FAQSection } from "./faq-section";

describe("FAQ section", () => {
  it("links the API answer to the developer docs", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <FAQSection />
      </LanguageProvider>,
    );

    await user.click(
      screen.getByText("Can I access Schemes.sg data through an API?"),
    );

    expect(
      await screen.findByRole("link", { name: "Read the developer docs" }),
    ).toHaveAttribute("href", "/developers");
  });

  it("links the privacy answer to the policy", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <FAQSection />
      </LanguageProvider>,
    );

    await user.click(screen.getByText("Is my personal information safe?"));

    expect(
      await screen.findByRole("link", { name: "Read our Privacy Policy" }),
    ).toHaveAttribute("href", "/privacy");
  });

  // The answers state what we do and do not share, so both links have to
  // survive translation, not only work in English.
  it("keeps both answer links in Chinese", async () => {
    const user = userEvent.setup();
    function LocaleButtons() {
      const { setLocale } = useLanguage();
      return (
        <>
          <button onClick={() => setLocale("zh")}>zh</button>
          <button onClick={() => setLocale("en")}>en</button>
        </>
      );
    }
    render(
      <LanguageProvider>
        <LocaleButtons />
        <FAQSection />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole("button", { name: "zh" }));
    try {
      await user.click(await screen.findByText("我的个人信息安全吗？"));
      expect(
        await screen.findByRole("link", { name: "阅读我们的隐私政策" }),
      ).toHaveAttribute("href", "/privacy");

      await user.click(
        screen.getByText("我可以通过应用程序接口获取 Schemes.sg 的数据吗？"),
      );
      expect(
        await screen.findByRole("link", { name: "请查看开发者文档" }),
      ).toHaveAttribute("href", "/developers");
    } finally {
      // The saved locale is module state; leave English for other tests.
      await user.click(screen.getByRole("button", { name: "en" }));
    }
  });
});
