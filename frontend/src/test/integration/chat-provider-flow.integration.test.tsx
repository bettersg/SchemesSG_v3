import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ChatPage from "@/components/chat/chat-page";
import { ChatProvider, useChat } from "@/providers";
import { catalogScheme } from "@/test/fixtures/catalog";
import {
  stubChatEnvironment,
  streamResponse,
} from "@/test/fixtures/chat-stream";
import { TEST_API_URL } from "@/test/mocks/handlers";
import { server } from "@/test/mocks/server";

vi.mock("@/lib/auth-gateway", () => ({
  getAuthToken: async () => "test-auth-token",
}));

function ChatJourney({
  message = "I need support",
  previousAnswer,
}: {
  message?: string;
  previousAnswer?: string;
}) {
  const chat = useChat();
  const [started, setStarted] = useState(false);

  // Mirrors ChatHome: it owns the "chat started" latch and ChatPage clears it
  // through onReset.
  if (started) return <ChatPage onReset={() => setStarted(false)} />;

  return (
    <button
      type="button"
      onClick={() => {
        chat.setMessages([
          ...(previousAnswer
            ? [{ type: "bot" as const, text: previousAnswer }]
            : []),
          { type: "user", text: message },
        ]);
        setStarted(true);
      }}
    >
      Start chat
    </button>
  );
}

beforeEach(stubChatEnvironment);

describe("chat provider flow", () => {
  it("commits a streamed answer, schemes, follow-ups, and rating", async () => {
    const feedbackRequests: unknown[] = [];
    server.use(
      http.post(`${TEST_API_URL}/agent_chat_message`, () =>
        streamResponse([
          {
            type: "action_message",
            data: {
              phase: "search",
              label: "Searching",
              message: "Checking schemes",
            },
          },
          {
            type: "status",
            data: { phase: "session_started", sessionID: "session-123" },
          },
          { type: "text", data: { text: "Here is support for your family." } },
          { type: "schemes_update", data: { schemes: [catalogScheme] } },
          {
            type: "followups",
            data: { items: { Housing: "Show housing support" } },
          },
        ]),
      ),
      http.post(`${TEST_API_URL}/feedback`, async ({ request }) => {
        feedbackRequests.push(await request.json());
        return HttpResponse.json({ success: true });
      }),
    );
    const user = userEvent.setup();
    render(
      <ChatProvider>
        <ChatJourney />
      </ChatProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Start chat" }));

    expect(
      (await screen.findAllByText("Here is support for your family.")).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole("link", {
        name: /Test Support Scheme, Community Support Agency/,
      }).length,
    ).toBeGreaterThan(0);

    await user.click(
      screen.getAllByLabelText("Housing: Show housing support")[0],
    );
    expect(screen.getAllByRole("textbox", { name: "" })[0]).toHaveValue(
      "Show housing support",
    );

    await user.click(
      screen.getAllByRole("button", { name: "Good response" })[0],
    );
    await waitFor(() => expect(feedbackRequests).toHaveLength(1));
    expect(feedbackRequests[0]).toEqual({
      source: "chat",
      sessionId: "session-123",
      messageIndex: 1,
      rating: "up",
    });
  });

  it("rolls a failed turn back into the composer for retry", async () => {
    server.use(
      http.post(
        `${TEST_API_URL}/agent_chat_message`,
        () => new HttpResponse(null, { status: 503 }),
      ),
    );
    const user = userEvent.setup();
    render(
      <ChatProvider>
        <ChatJourney
          message="I need urgent support"
          previousAnswer="Your earlier support answer"
        />
      </ChatProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Start chat" }));

    expect(
      (
        await screen.findAllByText(
          /connection dropped before the response finished/i,
        )
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByRole("textbox", { name: "" })[0]).toHaveValue(
      "I need urgent support",
    );
    expect(
      screen.getAllByText("Your earlier support answer").length,
    ).toBeGreaterThan(0);
  });
});
