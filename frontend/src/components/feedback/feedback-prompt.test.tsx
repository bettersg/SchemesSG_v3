import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import FeedbackPrompt from "./feedback-prompt";
import { I18nWrapper } from "@/test/i18n-wrapper";

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
      <I18nWrapper>
        <FeedbackPrompt
        variant="rating"
        text="A useful answer"
        onMsgRate={onMsgRate}
      />
      </I18nWrapper>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Helpful" }));
    expect(onMsgRate).toHaveBeenLastCalledWith("up");

    rerender(
      <I18nWrapper>
        <FeedbackPrompt
          variant="rating"
          text="A useful answer"
          rating="up"
          onMsgRate={onMsgRate}
        />
      </I18nWrapper>,
    );
    expect(
      screen.getByRole("button", { name: "Helpful" }),
    ).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Not helpful" }));
    expect(onMsgRate).toHaveBeenLastCalledWith("down");

    fireEvent.click(screen.getByRole("button", { name: "Copy response" }));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith("A useful answer"),
    );
    expect(screen.getByRole("button", { name: "Copied" })).toBeVisible();
  });

  it("links users to the contribution form", () => {
    render(
      <I18nWrapper>
        <FeedbackPrompt variant="contribution" />
      </I18nWrapper>,
    );

    expect(
      screen.getByRole("link", { name: "Contribute a new scheme" }),
    ).toHaveAttribute("href", "/contribute");
  });
});
