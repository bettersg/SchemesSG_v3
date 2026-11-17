import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ChatLanding from "@/components/chat/chat-landing";
import { LanguageToggle } from "@/components/landing/shared/language-toggle";
import { Trans } from "@lingui/react/macro";
import { LanguageProvider } from "@/lib/landing-i18n";
import { ChatProvider, useChat } from "@/providers";

function ChatStateProbe() {
  const { messages } = useChat();
  return <output aria-label="Saved chat">{messages[0]?.text ?? ""}</output>;
}

function LanguageStateProbe() {
  return (
    <output aria-label="Catalog label">
      <Trans>Catalogue</Trans>
    </output>
  );
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

    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));
    await user.click(screen.getByRole("menuitemradio", { name: "中文" }));
    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));

    expect(
      await screen.findByRole("menuitemradio", { name: "中文" }),
    ).toHaveAttribute(
      "aria-checked",
      "true",
    );
    await user.keyboard("{Escape}");
    expect(localStorage.getItem("schemes-lang")).toBe("zh");
    expect(document.documentElement.lang).toBe("zh-Hans");
    await waitFor(() =>
      expect(
        screen.getByRole("status", { name: "Catalog label" }),
      ).toHaveTextContent("目录"),
    );
  });

  it("switches to Tamil and persists the choice", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <LanguageToggle />
        <LanguageStateProbe />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));
    await user.click(screen.getByRole("menuitemradio", { name: "தமிழ்" }));
    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));

    expect(
      await screen.findByRole("menuitemradio", { name: "தமிழ்" }),
    ).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(localStorage.getItem("schemes-lang")).toBe("ta");
    expect(document.documentElement.lang).toBe("ta");
  });

  it("switches to Malay and persists the choice", async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <LanguageToggle />
        <LanguageStateProbe />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));
    await user.click(screen.getByRole("menuitemradio", { name: "Melayu" }));
    await user.click(screen.getByRole("button", { name: /English|中文|தமிழ்|Melayu/ }));

    expect(
      await screen.findByRole("menuitemradio", { name: "Melayu" }),
    ).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(localStorage.getItem("schemes-lang")).toBe("ms");
    expect(document.documentElement.lang).toBe("ms");
  });
});
