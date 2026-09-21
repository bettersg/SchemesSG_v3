import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ChatLanding from "@/components/chat/chat-landing";
import { LanguageToggle } from "@/components/landing/shared/language-toggle";
import { LanguageProvider, useLanguage } from "@/lib/landing-i18n";
import { ChatProvider, useChat } from "@/providers";

function ChatStateProbe() {
  const { messages } = useChat();
  return <output aria-label="Saved chat">{messages[0]?.text ?? ""}</output>;
}

function LanguageStateProbe() {
  const { t } = useLanguage();
  return <output aria-label="Catalog label">{t.nav.catalog}</output>;
}

afterEach(() => {
  document.documentElement.lang = "";
});

describe("landing state", () => {
  it("turns a category prompt into the first saved chat message", async () => {
    const onSubmitSuccess = vi.fn();
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <ChatProvider>
          <ChatLanding onSubmitSuccess={onSubmitSuccess} />
          <ChatStateProbe />
        </ChatProvider>
      </LanguageProvider>,
    );

    await user.click(
      screen.getByRole("button", { name: "Financial Assistance" }),
    );
    expect(screen.getByRole("textbox")).toHaveValue(
      "I need financial assistance",
    );
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(
      screen.getByRole("status", { name: "Saved chat" }),
    ).toHaveTextContent("I need financial assistance");
    expect(onSubmitSuccess).toHaveBeenCalledOnce();
  });

  it("persists the selected language and exposes translated state", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <LanguageToggle />
        <LanguageStateProbe />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole("radio", { name: "中文" }));

    expect(screen.getByRole("radio", { name: "中文" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(localStorage.getItem("schemes-lang")).toBe("zh");
    expect(document.documentElement.lang).toBe("zh-Hans");
    expect(
      screen.getByRole("status", { name: "Catalog label" }),
    ).not.toHaveTextContent("Catalog");
  });
});
