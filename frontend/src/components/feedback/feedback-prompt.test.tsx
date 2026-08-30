import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import FeedbackPrompt from "./feedback-prompt";

const originalClipboard = Object.getOwnPropertyDescriptor(
  navigator,
  "clipboard",
);

afterEach(() => {
  if (originalClipboard) {
    Object.defineProperty(navigator, "clipboard", originalClipboard);
  } else {
    Reflect.deleteProperty(navigator, "clipboard");
  }
});

describe("FeedbackPrompt", () => {
  it("rates and copies a completed chat response", async () => {
    const onMsgRate = vi.fn();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const { rerender } = render(
      <FeedbackPrompt
        variant="rating"
        text="A useful answer"
        onMsgRate={onMsgRate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Good response" }));
    expect(onMsgRate).toHaveBeenLastCalledWith("up");

    rerender(
      <FeedbackPrompt
        variant="rating"
        text="A useful answer"
        rating="up"
        onMsgRate={onMsgRate}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Good response" }),
    ).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Bad response" }));
    expect(onMsgRate).toHaveBeenLastCalledWith("down");

    fireEvent.click(screen.getByRole("button", { name: "Copy response" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith("A useful answer"),
    );
    expect(screen.getByRole("button", { name: "Copied" })).toBeVisible();
  });

  it("links users to the contribution form", () => {
    render(<FeedbackPrompt variant="contribution" />);

    expect(
      screen.getByRole("link", { name: "Contribute a new scheme" }),
    ).toHaveAttribute("href", "/contribute");
  });
});
