import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChatHome from "@/components/chat/chat-home";
import { LanguageProvider } from "@/lib/landing-i18n";
import { ChatProvider } from "@/providers";
import {
  stubChatEnvironment,
  streamResponse,
} from "@/test/fixtures/chat-stream";
import { TEST_API_URL } from "@/test/mocks/handlers";
import { server } from "@/test/mocks/server";

vi.mock("@/lib/auth-gateway", () => ({
  getAuthToken: async () => "test-auth-token",
}));

const COMPOSER_PLACEHOLDER = "Ask a follow-up question…";

function renderChatHome() {
  return render(
    <LanguageProvider>
      <ChatProvider>
        <ChatHome />
      </ChatProvider>
    </LanguageProvider>,
  );
}

async function submitFromLanding(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Financial Assistance" }));
  await user.click(screen.getByRole("button", { name: "Search" }));
}

beforeEach(stubChatEnvironment);

describe("chat home", () => {
  it("keeps the chat view and its error when the first send fails", async () => {
    server.use(
      http.post(
        `${TEST_API_URL}/agent_chat_message`,
        () => new HttpResponse(null, { status: 503 }),
      ),
    );
    const user = userEvent.setup();
    renderChatHome();

    await submitFromLanding(user);

    // The rollback empties `messages` again; without ChatHome's latch the
    // landing screen swaps back in and takes this alert with it.
    expect((await screen.findAllByRole("alert")).length).toBeGreaterThan(0);
    expect(
      screen.getAllByPlaceholderText(COMPOSER_PLACEHOLDER).length,
    ).toBeGreaterThan(0);
    expect(
      screen.queryByRole("button", { name: "Search" }),
    ).not.toBeInTheDocument();

    // "New Chat" is the one path that clears the latch.
    await user.click(screen.getAllByRole("button", { name: "Start new chat" })[0]);
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(
      await screen.findByRole("button", { name: "Search" }),
    ).toBeInTheDocument();
  });

  it("claims a follow-up send before its response starts so a retry cannot abort it", async () => {
    let chatRequests = 0;
    let releaseFollowUp!: () => void;
    const followUpGate = new Promise<void>((resolve) => {
      releaseFollowUp = resolve;
    });
    server.use(
      http.post(`${TEST_API_URL}/agent_chat_message`, async () => {
        chatRequests += 1;
        if (chatRequests === 1) {
          return streamResponse([
            { type: "text", data: { text: "Here is the financial support." } },
          ]);
        }
        // Headers stay pending, standing in for a slow connection.
        await followUpGate;
        return streamResponse([
          { type: "text", data: { text: "Here is the housing support." } },
        ]);
      }),
    );
    const user = userEvent.setup();
    renderChatHome();

    await submitFromLanding(user);
    await screen.findAllByText("Here is the financial support.");

    // The first turn is done, so the composer is live again — this is the send
    // whose in-flight window used to be unguarded.
    await user.type(
      screen.getAllByPlaceholderText(COMPOSER_PLACEHOLDER)[0],
      "what about housing{Enter}",
    );
    await waitFor(() => expect(chatRequests).toBe(2));

    // In flight but not a byte of the response yet: the send has to be claimed
    // synchronously, otherwise a second one starts and aborts this request,
    // stranding its user message with no reply.
    for (const composer of screen.getAllByPlaceholderText(
      COMPOSER_PLACEHOLDER,
    )) {
      expect(composer).toBeDisabled();
    }
    await user.type(
      screen.getAllByPlaceholderText(COMPOSER_PLACEHOLDER)[0],
      "and transport{Enter}",
    );
    expect(chatRequests).toBe(2);

    releaseFollowUp();

    expect(
      (await screen.findAllByText("Here is the housing support.")).length,
    ).toBeGreaterThan(0);
    expect(chatRequests).toBe(2);
  });
});
