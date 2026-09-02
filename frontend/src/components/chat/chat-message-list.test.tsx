import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ChatMessageList from "./chat-message-list";
import { THINKING_PHRASES } from "./thinking-phrases";

// The spinner is a canvas/wasm Lottie player with nothing to assert on, and
// letting it fetch its animation would trip the suite's unhandled-request guard.
vi.mock("@lottiefiles/dotlottie-react", () => ({
  DotLottieReact: () => <div data-testid="chat-spinner" />,
  // ChatSpinner calls this at module scope to point the player at the
  // self-hosted wasm runtime; the mock has to carry it or the import throws.
  setWasmUrl: () => {},
}));

const userTurn = [{ type: "user" as const, text: "i need help with preschool fees" }];

describe("ChatMessageList", () => {
  it("shows the thinking indicator the moment generation starts, with no stream data yet", () => {
    // This is the regression guard for the original bug: the indicator used to
    // wait for the first status step or text chunk to arrive over the network.
    render(
      <ChatMessageList
        messages={userTurn}
        streamingBlocks={[]}
        statusSteps={[]}
        isGenerating
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Working on your answer");
    expect(screen.getByText(THINKING_PHRASES[0])).toBeInTheDocument();
    expect(screen.getByTestId("chat-spinner")).toBeInTheDocument();
  });

  it("announces a real status step instead of the placeholder once one arrives", () => {
    render(
      <ChatMessageList
        messages={userTurn}
        streamingBlocks={[]}
        statusSteps={[
          { id: "1", label: "Searching schemes", message: "Searched for preschool fees" },
        ]}
        isGenerating
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("Searching schemes");
    expect(screen.queryByText(THINKING_PHRASES[0])).not.toBeInTheDocument();
  });

  it("hides the indicator when nothing is generating", () => {
    render(
      <ChatMessageList
        messages={[...userTurn, { type: "bot", text: "Here is what I found." }]}
        streamingBlocks={[]}
        statusSteps={[]}
      />,
    );

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(screen.queryByText(THINKING_PHRASES[0])).not.toBeInTheDocument();
  });
});
