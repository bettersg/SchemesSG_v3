import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LanguageProvider } from "@/lib/landing-i18n";
import { ChatProvider, useChat } from "@/providers/chat-provider";
import { CHAT_STORAGE_KEYS } from "@/lib/chat-storage";
import { Navbar } from "./navbar";

const navigation = vi.hoisted(() => ({ pathname: "/catalog" }));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
}));

afterEach(() => {
  navigation.pathname = "/catalog";
  sessionStorage.clear();
});

function ResetModalProbe() {
  const { hasActiveChat, resetModalIsOpen } = useChat();
  return <output data-active={hasActiveChat} data-confirm={resetModalIsOpen} />;
}

async function renderNavbar({
  pathname,
  activeChat,
}: {
  pathname: string;
  activeChat: boolean;
}) {
  navigation.pathname = pathname;
  if (activeChat) {
    sessionStorage.setItem(
      CHAT_STORAGE_KEYS.messages,
      JSON.stringify([{ type: "user", text: "help with rent" }]),
    );
  }
  const view = render(
    <LanguageProvider>
      <ChatProvider>
        <Navbar />
        <ResetModalProbe />
      </ChatProvider>
    </LanguageProvider>,
  );
  const probe = view.container.querySelector("output")!;
  // The provider restores the chat from sessionStorage after mount.
  await vi.waitFor(() => expect(probe.dataset.active).toBe(String(activeChat)));
  const logo = view.container.querySelector<HTMLAnchorElement>('a[href="/"]')!;
  return { probe, logo };
}

describe("Navbar", () => {
  it("opens and closes the mobile navigation with core routes available", async () => {
    const user = userEvent.setup();
    const { unmount } = render(
      <LanguageProvider>
        <ChatProvider>
          <Navbar />
        </ChatProvider>
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

  it("offers a reset from the logo during a chat on the search page", async () => {
    const { probe, logo } = await renderNavbar({
      pathname: "/",
      activeChat: true,
    });

    // fireEvent.click returns false when a handler cancels the navigation.
    expect(fireEvent.click(logo)).toBe(false);
    expect(probe.dataset.confirm).toBe("true");
  });

  it("offers a reset from the Search tab during a chat", async () => {
    const { probe } = await renderNavbar({ pathname: "/", activeChat: true });

    const searchTab = screen.getByRole("link", { name: /Search Schemes/ });
    expect(fireEvent.click(searchTab)).toBe(false);
    expect(probe.dataset.confirm).toBe("true");
  });

  it("navigates straight to search when there is no chat", async () => {
    const { probe, logo } = await renderNavbar({
      pathname: "/",
      activeChat: false,
    });

    expect(fireEvent.click(logo)).toBe(true);
    expect(probe.dataset.confirm).toBe("false");
  });

  it("navigates straight to search from another page, chat or not", async () => {
    const { probe, logo } = await renderNavbar({
      pathname: "/catalog",
      activeChat: true,
    });

    expect(fireEvent.click(logo)).toBe(true);
    expect(probe.dataset.confirm).toBe("false");
  });
});
